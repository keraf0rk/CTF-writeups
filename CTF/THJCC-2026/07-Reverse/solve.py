#!/usr/bin/env python3
"""THJCC 2026 Summer - "xorlocks" solver.

``xorlock`` is a 1256-byte static, stripped ELF (x86-64, raw syscalls). It takes a
20-character password in argv[1] and checks it byte by byte against a table in
``.rodata``; the check is position-dependent but fully invertible:

    ((password[i] ^ 0x5A) + 3 * i) & 0xFF == table[i]

so ``password[i] = ((table[i] - 3 * i) & 0xFF) ^ 0x5A``.

The flag is stored separately in ``.rodata`` under the same rolling-XOR stream the
author reuses across this event (base VA 0x200170, key starts at 0x40, step 0x1A, even
byte of each pair uses ``key - 0x0D``), so it can be lifted without the password.

Usage:
    python3 solve.py --binary xorlock
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path
from typing import NamedTuple

from loguru import logger

TABLE_VA: int = 0x200150
PASSWORD_LEN: int = 20
PASSWORD_XOR: int = 0x5A
PASSWORD_STEP: int = 3

FLAG_VA: int = 0x200170
FLAG_LEN: int = 31
FLAG_KEY_START: int = 0x40
FLAG_KEY_STEP: int = 0x1A
FLAG_EVEN_BIAS: int = 0x0D

EXPECTED_PASSWORD: bytes = b"xor_me_if_you_can_26"
EXPECTED_FLAG: str = "THJCC{xor_basics_are_not_magic}"


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


def recover_password(table: bytes) -> bytes:
    """Invert the position-dependent XOR/ADD check."""
    return bytes(((table[i] - PASSWORD_STEP * i) & 0xFF) ^ PASSWORD_XOR for i in range(len(table)))


def verify_password(table: bytes, candidate: bytes) -> bool:
    """Replay the binary's forward check on a candidate password."""
    if len(candidate) != len(table):
        return False
    return all(
        ((candidate[i] ^ PASSWORD_XOR) + PASSWORD_STEP * i) & 0xFF == table[i]
        for i in range(len(table))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path(__file__).with_name("xorlock"),
        help="path to the ELF challenge binary",
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

    table_offset = va_to_offset(sections, TABLE_VA)
    table = blob[table_offset : table_offset + PASSWORD_LEN]
    logger.info("check table at VA {:#x}: {}", TABLE_VA, table.hex())

    password = recover_password(table)
    if not verify_password(table, password):
        logger.error("recovered password fails the forward check")
        return 1
    logger.success("password = {}", password.decode())

    flag_offset = va_to_offset(sections, FLAG_VA)
    flag = decode_rolling_xor(
        blob[flag_offset : flag_offset + FLAG_LEN],
        FLAG_KEY_START,
        FLAG_KEY_STEP,
        FLAG_EVEN_BIAS,
    ).decode()
    logger.success("flag = {}", flag)

    if password != EXPECTED_PASSWORD or flag != EXPECTED_FLAG:
        logger.error("does not match the known-good password/flag")
        return 1
    logger.success("matches the known-good password and flag")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
