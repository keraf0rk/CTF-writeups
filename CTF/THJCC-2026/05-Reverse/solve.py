#!/usr/bin/env python3
"""THJCC 2026 Summer - "License" solver.

``license_v2`` is a 3.6 KB static, stripped ELF (x86-64, no libc, raw syscalls). It
validates a 29-character key and only then prints the flag. The flag, however, is not
derived from the key: it sits in ``.rodata`` under a rolling-XOR stream and is printed
verbatim, so it can be recovered statically without ever producing a valid license.

Flag stream (loop at 0x201615, base VA 0x200210): key starts at 0x7E and grows by 0x1A
per byte pair; the even byte of a pair is XOR-ed with ``key - 0x0D``, the odd one with
``key``. 31 bytes are emitted.

The script also re-states the key format the binary enforces, all of it read off the
checks at 0x201264-0x2012F8:

* ``strlen(argv[1]) == 29``;
* ``'-'`` at indexes 4, 9, 14, 19, 24 (the test is ``5*floor((i+1)/5) - 1 == i``);
* every other character is a hex digit (``0-9``, ``A-F``, ``a-f``) -> 24 nibbles.

Usage:
    python3 solve.py --binary license_v2
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path
from typing import NamedTuple

from loguru import logger

FLAG_VA: int = 0x200210
FLAG_LEN: int = 31
FLAG_KEY_START: int = 0x7E
FLAG_KEY_STEP: int = 0x1A
FLAG_EVEN_BIAS: int = 0x0D

KEY_LENGTH: int = 29
DASH_POSITIONS: tuple[int, ...] = (4, 9, 14, 19, 24)
HEX_DIGITS: str = "0123456789abcdefABCDEF"

EXPECTED_FLAG: str = "THJCC{license_pipeline_rebuilt}"


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


def is_well_formed_key(candidate: str) -> bool:
    """Replicate the binary's purely syntactic key check (not the cryptographic one)."""
    if len(candidate) != KEY_LENGTH:
        return False
    for index, char in enumerate(candidate):
        if index in DASH_POSITIONS:
            if char != "-":
                return False
        elif char not in HEX_DIGITS:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path(__file__).with_name("license_v2"),
        help="path to the ELF challenge binary",
    )
    parser.add_argument(
        "--check-key",
        default=None,
        metavar="KEY",
        help="run a candidate key through the syntactic format check only",
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
    logger.info("sections: {}", ", ".join(s.name for s in sections if s.name))

    if args.check_key is not None:
        verdict = "well-formed" if is_well_formed_key(args.check_key) else "rejected"
        logger.info("key {!r} is {} (format only)", args.check_key, verdict)

    offset = va_to_offset(sections, FLAG_VA)
    logger.info("flag blob: VA {:#x} -> file offset {:#x}, {} bytes", FLAG_VA, offset, FLAG_LEN)

    flag = decode_rolling_xor(
        blob[offset : offset + FLAG_LEN],
        FLAG_KEY_START,
        FLAG_KEY_STEP,
        FLAG_EVEN_BIAS,
    ).decode()

    logger.info("key format: 29 chars, '-' at {}, rest hex", ", ".join(map(str, DASH_POSITIONS)))
    logger.info("note: the 0x31415926 hash at 0x201398 is computed but never used")
    logger.success("flag = {}", flag)
    if flag != EXPECTED_FLAG:
        logger.error("does not match the known-good flag")
        return 1
    logger.success("matches the known-good flag")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
