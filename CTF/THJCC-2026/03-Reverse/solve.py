"""Solver for THJCC CTF 2026 - "Because There is no one Make Reverse So I Create This Chal".

The Mach-O arm64 binary keeps a 708-byte XTEA-encrypted payload inside ``__TEXT,__const``.
The payload is a small bytecode program whose only job is to compare a transformed copy
of the user input against hard-coded constants, one input byte per chain.

Pipeline implemented here:

1. parse the Mach-O load commands to locate ``__TEXT,__const``;
2. rebuild the XTEA keystream (``v0 = block_index + 0xAFD9E340``, ``v1 = 0x1E403058``)
   and decrypt the payload;
3. verify the FNV-1a checksum the binary itself validates (``0x4B9FB9F7``);
4. disassemble the bytecode and brute-force every input byte independently.

Usage::

    python3 solve.py [path/to/chal]
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path
from typing import Final, NamedTuple

from loguru import logger

MASK32: Final[int] = 0xFFFFFFFF
XTEA_DELTA: Final[int] = 0x9E3779B9
XTEA_ROUNDS: Final[int] = 32
NONCE_BASE: Final[int] = 0xAFD9E340
NONCE_V1: Final[int] = 0x1E403058
PAYLOAD_SIZE: Final[int] = 0x2C4
FNV_OFFSET_BASIS: Final[int] = 0x811C9DC5
FNV_PRIME: Final[int] = 0x01000193
FNV_EXPECTED: Final[int] = 0x4B9FB9F7

OP_LOAD: Final[int] = 0x86
OP_HALT_OK: Final[int] = 0x5A
OP_SET_PTR: Final[int] = 0x97
OP_ADD: Final[int] = 0x18
OP_XOR: Final[int] = 0x15
OP_SUB: Final[int] = 0xE5
OP_ROL: Final[int] = 0x74
OP_CHECK: Final[int] = 0x8F
OP_CHECK_LEN: Final[int] = 0xCD
OP_JMP: Final[int] = 0x5B

LC_SEGMENT_64: Final[int] = 0x19


class Section(NamedTuple):
    """A Mach-O section: virtual address, file offset and size."""

    name: str
    addr: int
    offset: int
    size: int


def find_section(blob: bytes, segment: str, section: str) -> Section:
    """Return the requested ``segment,section`` from a 64-bit Mach-O image."""
    ncmds = struct.unpack_from("<I", blob, 16)[0]
    cursor = 32
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from("<II", blob, cursor)
        if cmd == LC_SEGMENT_64:
            seg_name = blob[cursor + 8 : cursor + 24].rstrip(b"\0").decode()
            nsects = struct.unpack_from("<I", blob, cursor + 64)[0]
            sect_cursor = cursor + 72
            for _ in range(nsects):
                sect_name = blob[sect_cursor : sect_cursor + 16].rstrip(b"\0").decode()
                if seg_name == segment and sect_name == section:
                    addr, size = struct.unpack_from("<QQ", blob, sect_cursor + 32)
                    offset = struct.unpack_from("<I", blob, sect_cursor + 48)[0]
                    return Section(f"{seg_name},{sect_name}", addr, offset, size)
                sect_cursor += 80
        cursor += cmdsize
    raise LookupError(f"section {segment},{section} not found")


def xtea_encipher(v0: int, v1: int, key: tuple[int, ...]) -> tuple[int, int]:
    """Standard 32-round XTEA block encipher, used here to build the keystream."""
    total = 0
    for _ in range(XTEA_ROUNDS):
        v0 = (v0 + ((((v1 << 4) & MASK32) ^ (v1 >> 5)) + v1 ^ (total + key[total & 3]))) & MASK32
        total = (total + XTEA_DELTA) & MASK32
        v1 = (v1 + ((((v0 << 4) & MASK32) ^ (v0 >> 5)) + v0 ^ (total + key[(total >> 11) & 3]))) & MASK32
    return v0, v1


def decrypt_payload(blob: bytes) -> bytes:
    """Decrypt the 708-byte VM payload stored in ``__TEXT,__const``."""
    const = find_section(blob, "__TEXT", "__const")
    body = blob[const.offset : const.offset + const.size]
    ciphertext = body[:PAYLOAD_SIZE]
    key_a = struct.unpack_from("<4I", body, PAYLOAD_SIZE)
    key_b = struct.unpack_from("<4I", body, PAYLOAD_SIZE + 16)
    key = tuple(a ^ b for a, b in zip(key_a, key_b))
    logger.info("XTEA key: {}", " ".join(f"{word:#010x}" for word in key))

    keystream = bytearray()
    for block in range(len(ciphertext) // 8 + 1):
        v0, v1 = xtea_encipher((block + NONCE_BASE) & MASK32, NONCE_V1, key)
        keystream += struct.pack("<II", v0, v1)
    return bytes(a ^ b for a, b in zip(ciphertext, keystream))


def fnv1a_32(data: bytes) -> int:
    """FNV-1a 32-bit hash, the payload integrity check performed by the binary."""
    digest = FNV_OFFSET_BASIS
    for byte in data:
        digest = ((digest ^ byte) * FNV_PRIME) & MASK32
    return digest


def parse_bytecode(code: bytes) -> tuple[int, dict[int, list[tuple[str, int]]]]:
    """Return the expected input length and the per-position operation chains."""
    chains: dict[int, list[tuple[str, int]]] = {}
    length = 0
    pointer = -1
    pc = 0
    while pc < len(code):
        op = code[pc]
        if op == OP_LOAD:
            pc += 1
        elif op == OP_HALT_OK:
            break
        elif op == OP_SET_PTR:
            pointer = code[pc + 1]
            chains[pointer] = []
            pc += 2
        elif op == OP_ADD:
            chains[pointer].append(("+", code[pc + 1]))
            pc += 2
        elif op == OP_SUB:
            chains[pointer].append(("-", code[pc + 1]))
            pc += 2
        elif op == OP_XOR:
            chains[pointer].append(("^", code[pc + 1]))
            pc += 2
        elif op == OP_ROL:
            chains[pointer].append(("rol", code[pc + 1] & 7))
            pc += 2
        elif op == OP_CHECK:
            chains[pointer].append(("==", code[pc + 1]))
            pc += 2
        elif op == OP_CHECK_LEN:
            length = code[pc + 1]
            pc += 2
        elif op == OP_JMP:
            pc = pc + code[pc + 1] + 2
        else:
            raise ValueError(f"unknown opcode {op:#04x} at {pc:#06x}")
    return length, chains


def apply_chain(value: int, ops: list[tuple[str, int]]) -> int:
    """Run one input byte through its transformation chain (checks excluded)."""
    for kind, operand in ops:
        if kind == "+":
            value = (value + operand) & 0xFF
        elif kind == "-":
            value = (value - operand) & 0xFF
        elif kind == "^":
            value ^= operand
        elif kind == "rol" and operand:
            value = ((value << operand) | (value >> (8 - operand))) & 0xFF
    return value


def recover_flag(code: bytes) -> bytes:
    """Brute-force each input byte against its own chain - 256 candidates per position."""
    length, chains = parse_bytecode(code)
    logger.info("VM expects {} input bytes", length)
    flag = bytearray(length)
    for index in range(length):
        ops = chains[index]
        target = ops[-1][1]
        for candidate in range(256):
            if apply_chain(candidate, ops[:-1]) == target:
                flag[index] = candidate
                break
        else:
            raise ValueError(f"no candidate for byte {index}")
    return bytes(flag)


def main() -> None:
    """Entry point: decrypt the payload, verify it and print the flag."""
    binary_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("chal")
    blob = binary_path.read_bytes()
    logger.info("loaded {} ({} bytes)", binary_path.name, len(blob))

    payload = decrypt_payload(blob)
    digest = fnv1a_32(payload)
    logger.info("FNV-1a of payload: {:#010x} (expected {:#010x})", digest, FNV_EXPECTED)
    if digest != FNV_EXPECTED:
        raise SystemExit("payload checksum mismatch - decryption is wrong")

    flag = recover_flag(payload)
    logger.success("FLAG: {}", flag.decode())


if __name__ == "__main__":
    main()
