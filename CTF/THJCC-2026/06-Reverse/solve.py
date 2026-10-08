#!/usr/bin/env python3
"""THJCC 2026 Summer - "404" solver.

``404`` is a 2 KB static, stripped ELF (x86-64, raw syscalls). It copies 0x121 bytes of
bytecode onto the stack and runs them in a tiny register VM that validates a 16-byte
argv[1]. Opcode 7 of that VM is literally "print the flag", and the flag itself lives in
``.rodata`` under the same rolling-XOR stream the author reuses across this event, so the
flag is recoverable without solving the VM at all.

VM opcode table (jump table at VA 0x200240, every instruction is 3 bytes):

===== ========== ==========================================
code   handler    meaning
===== ========== ==========================================
  1    0x20142F   reg[b] = input[c]        (b < 8, c < 16)
  2    0x2014EE   reg[b] ^= imm
  3    0x201494   reg[b] += imm
  4    0x2014B7   reg[b] = rol8(reg[b], imm & 7)
  5    0x201465   flag = (reg[b] == imm)
  6    0x201523   if not flag: reject
  7    0x201615   print the flag
  8    0x20150A   relative jump
===== ========== ==========================================

The bytecode is 16 identical 18-byte blocks (LOAD, XOR, ADD, ROL, CMP, CHECK) plus a
trailing opcode 7, and each block reads exactly one input byte - so the accepted input
inverts byte by byte: ``in[i] = (ror8(target, rot) - add) ^ xor``.

Usage:
    python3 solve.py --binary 404              # flag only, no third-party RE deps
    python3 solve.py --recover-input           # also rebuild the accepted argv[1]
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path
from typing import NamedTuple

from loguru import logger

FLAG_VA: int = 0x200280
FLAG_LEN: int = 32
FLAG_KEY_START: int = 0x35
FLAG_KEY_STEP: int = 0x1A
FLAG_EVEN_BIAS: int = 0x0D

BYTECODE_SIZE: int = 0x121
STACK_BASE: int = 0x70
BLOCK_SIZE: int = 18
INPUT_LENGTH: int = 16

EXPECTED_FLAG: str = "THJCC{vm_bytecode_is_a_contract}"
EXPECTED_INPUT: bytes = b"vm_is_not_magic!"


class Elf64Section(NamedTuple):
    """Minimal ELF64 section descriptor."""

    name: str
    addr: int
    offset: int
    size: int


def read_sections(blob: bytes) -> list[Elf64Section]:
    """Parse the ELF64 section header table."""
    shoff = struct.unpack_from("<Q", blob, 0x28)[0]
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", blob, 0x3A)
    str_off = struct.unpack_from("<Q", blob, shoff + shstrndx * shentsize + 0x18)[0]
    sections: list[Elf64Section] = []
    for index in range(shnum):
        base = shoff + index * shentsize
        name_ptr = struct.unpack_from("<I", blob, base)[0]
        addr, offset, size = struct.unpack_from("<QQQ", blob, base + 0x10)
        end = blob.index(b"\0", str_off + name_ptr)
        sections.append(Elf64Section(blob[str_off + name_ptr : end].decode(), addr, offset, size))
    return sections


def section_by_name(sections: list[Elf64Section], name: str) -> Elf64Section:
    """Return a section by name."""
    for section in sections:
        if section.name == name:
            return section
    raise LookupError(f"section {name} not found")


def va_to_offset(sections: list[Elf64Section], va: int) -> int:
    """Translate a virtual address into a file offset."""
    for section in sections:
        if section.addr and section.addr <= va < section.addr + section.size:
            return section.offset + (va - section.addr)
    raise LookupError(f"virtual address {va:#x} is not mapped by any section")


def decode_rolling_xor(data: bytes, key_start: int, key_step: int, even_bias: int) -> bytes:
    """Undo the author's rolling-XOR stream (identical in License / 404 / xorlocks)."""
    out = bytearray()
    key = key_start
    for pair_index in range(0, len(data), 2):
        out.append(data[pair_index] ^ ((key - even_bias) & 0xFF))
        if pair_index + 1 < len(data):
            out.append(data[pair_index + 1] ^ key)
        key = (key + key_step) & 0xFF
    return bytes(out)


def rol8(value: int, count: int) -> int:
    """Rotate an 8-bit value left."""
    count &= 7
    if count == 0:
        return value & 0xFF
    return ((value << count) | (value >> (8 - count))) & 0xFF


def ror8(value: int, count: int) -> int:
    """Rotate an 8-bit value right."""
    count &= 7
    if count == 0:
        return value & 0xFF
    return ((value >> count) | (value << (8 - count))) & 0xFF


def reconstruct_bytecode(blob: bytes, sections: list[Elf64Section]) -> bytes:
    """Rebuild the stack image of the VM program by replaying the loader in .text.

    The loader is a run of ``movaps xmm0, [rip + X]`` / ``movaps [rsp + D], xmm0`` pairs
    plus one ``mov byte [rsp + D], imm`` for the trailing opcode. Requires capstone.
    """
    from capstone import CS_ARCH_X86, CS_MODE_64, Cs
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP, X86_REG_RSP

    text = section_by_name(sections, ".text")
    engine = Cs(CS_ARCH_X86, CS_MODE_64)
    engine.detail = True

    code = bytearray(BYTECODE_SIZE)
    source: int | None = None
    inside_loader = False
    for insn in engine.disasm(blob[text.offset : text.offset + text.size], text.addr):
        operands = insn.operands
        matched = False
        if insn.mnemonic == "movaps" and len(operands) == 2:
            dst, src = operands
            if src.type == X86_OP_MEM and src.mem.base == X86_REG_RIP:
                source = insn.address + insn.size + src.mem.disp
                matched = True
            elif dst.type == X86_OP_MEM and dst.mem.base == X86_REG_RSP and source is not None:
                index = dst.mem.disp + STACK_BASE
                offset = va_to_offset(sections, source)
                code[index : index + 16] = blob[offset : offset + 16]
                inside_loader = True
                matched = True
        elif insn.mnemonic == "mov" and len(operands) == 2 and inside_loader:
            dst, src = operands
            if (
                dst.type == X86_OP_MEM
                and dst.mem.base == X86_REG_RSP
                and src.type == X86_OP_IMM
                and insn.op_str.startswith("byte ptr")
                and 0 <= dst.mem.disp + STACK_BASE < BYTECODE_SIZE
            ):
                code[dst.mem.disp + STACK_BASE] = src.imm & 0xFF
                matched = True
        if inside_loader and not matched:
            # The loader is one uninterrupted run of stores; anything else ends it.
            break
    logger.info("rebuilt {} bytes of vm bytecode", len(code))
    return bytes(code)


def recover_input(code: bytes) -> bytes:
    """Invert the 16 per-byte validation blocks into the accepted argv[1]."""
    accepted = bytearray(INPUT_LENGTH)
    for block_index in range(INPUT_LENGTH):
        block = code[block_index * BLOCK_SIZE : (block_index + 1) * BLOCK_SIZE]
        opcodes = (block[0], block[3], block[6], block[9], block[12], block[15])
        if opcodes != (1, 2, 3, 4, 5, 6):
            raise ValueError(f"unexpected block layout at {block_index}: {opcodes}")
        position, key, addend, rotation, target = block[2], block[5], block[8], block[11], block[14]
        value = ror8(target, rotation)
        value = (value - addend) & 0xFF
        accepted[position] = value ^ key
    return bytes(accepted)


def verify_input(code: bytes, candidate: bytes) -> bool:
    """Replay the VM's forward transformation to confirm the recovered input."""
    for block_index in range(INPUT_LENGTH):
        block = code[block_index * BLOCK_SIZE : (block_index + 1) * BLOCK_SIZE]
        position, key, addend, rotation, target = block[2], block[5], block[8], block[11], block[14]
        value = candidate[position] ^ key
        value = (value + addend) & 0xFF
        if rol8(value, rotation) != target:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path(__file__).with_name("404"),
        help="path to the ELF challenge binary",
    )
    parser.add_argument(
        "--recover-input",
        action="store_true",
        help="also rebuild the VM bytecode and invert the accepted argv[1] (needs capstone)",
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level: <7}</level> {message}")

    if not args.binary.is_file():
        logger.error("no such file: {}", args.binary)
        return 1

    blob = args.binary.read_bytes()
    logger.info("loaded {} ({} bytes)", args.binary.name, len(blob))
    sections = read_sections(blob)

    if args.recover_input:
        code = reconstruct_bytecode(blob, sections)
        accepted = recover_input(code)
        if not verify_input(code, accepted):
            logger.error("recovered input fails the forward check")
            return 1
        logger.success("accepted argv[1] = {}", accepted.decode())
        if accepted != EXPECTED_INPUT:
            logger.error("does not match the known-good input")
            return 1

    offset = va_to_offset(sections, FLAG_VA)
    logger.info("flag blob: VA {:#x} -> file offset {:#x}, {} bytes", FLAG_VA, offset, FLAG_LEN)
    flag = decode_rolling_xor(
        blob[offset : offset + FLAG_LEN],
        FLAG_KEY_START,
        FLAG_KEY_STEP,
        FLAG_EVEN_BIAS,
    ).decode()

    logger.success("flag = {}", flag)
    if flag != EXPECTED_FLAG:
        logger.error("does not match the known-good flag")
        return 1
    logger.success("matches the known-good flag")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
