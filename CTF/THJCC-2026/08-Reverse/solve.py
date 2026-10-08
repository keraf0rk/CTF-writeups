#!/usr/bin/env python3
"""THJCC 2026 Summer - "TeaGod.exe" solver.

``TeaGod.exe`` is a MinGW-built PE32+ GUI application: a window with a "WORSHIP TEA GOD"
button. Clicking it increments a counter in ``.data`` and unlocks a "reward" - the flag.
The gate is only ``counter != 0``, so the 666 worships in the challenge description are
flavour text; one click is enough.

The reward is decrypted in two layers.

Layer 1 (loop at 0x140001E90): three 12-byte blobs, reachable through the pointer table
at VA 0x140005210, with one key byte each at VA 0x140005228::

    tmp[i] = ((cipher[i] + (0xE7 - 7 * i)) & 0xFF) ^ key[chunk]

Layer 2 (loop at 0x140001FD0): an 8-byte key ``0x616E7368655F6368`` -> ``b"hc_ehsna"``,
indexed by ``(1 + 3 * i) & 7``::

    flag[i] = tmp[i] ^ key8[(1 + 3 * i) & 7]

The same loop XOR-s every byte twice with a value returned by the anti-analysis routine at
0x140002E10 - two XORs with the same byte cancel, so that runtime value can be ignored
entirely when solving statically.

Usage:
    python3 solve.py --binary TeaGod.exe
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path
from typing import NamedTuple

from loguru import logger

POINTER_TABLE_VA: int = 0x140005210
KEY_TABLE_VA: int = 0x140005228
CHUNK_COUNT: int = 3
CHUNK_SIZE: int = 12

LAYER1_BIAS: int = 0xE7
LAYER1_STEP: int = 7
LAYER2_KEY: int = 0x616E7368655F6368
LAYER2_STRIDE: int = 3
LAYER2_OFFSET: int = 1

EXPECTED_FLAG: str = "THJCC{h77p5://p4s73b1n.com/R58uv133}"


class PeSection(NamedTuple):
    """Minimal PE section descriptor."""

    name: str
    va: int
    raw_offset: int
    raw_size: int


def read_sections(blob: bytes) -> tuple[int, list[PeSection]]:
    """Return the image base and the section table of a PE32+ image."""
    pe_offset = struct.unpack_from("<I", blob, 0x3C)[0]
    if blob[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("not a PE image")
    section_count = struct.unpack_from("<H", blob, pe_offset + 6)[0]
    opt_size = struct.unpack_from("<H", blob, pe_offset + 20)[0]
    opt_offset = pe_offset + 24
    image_base = struct.unpack_from("<Q", blob, opt_offset + 24)[0]

    sections: list[PeSection] = []
    table = opt_offset + opt_size
    for index in range(section_count):
        entry = table + index * 40
        name = blob[entry : entry + 8].rstrip(b"\0").decode()
        _, virtual_address, raw_size, raw_offset = struct.unpack_from("<IIII", blob, entry + 8)
        sections.append(PeSection(name, image_base + virtual_address, raw_offset, raw_size))
    return image_base, sections


def va_to_offset(sections: list[PeSection], va: int) -> int:
    """Translate a virtual address into a file offset."""
    for section in sections:
        if section.va <= va < section.va + section.raw_size:
            return section.raw_offset + (va - section.va)
    raise LookupError(f"virtual address {va:#x} is not mapped by any section")


def read_at(blob: bytes, sections: list[PeSection], va: int, size: int) -> bytes:
    """Read ``size`` bytes at a virtual address."""
    offset = va_to_offset(sections, va)
    return blob[offset : offset + size]


def decrypt_layer1(blob: bytes, sections: list[PeSection]) -> bytes:
    """Undo the per-chunk ``(cipher + (0xE7 - 7*i)) ^ key`` transformation."""
    keys = read_at(blob, sections, KEY_TABLE_VA, CHUNK_COUNT)
    logger.info("layer-1 chunk keys: {}", keys.hex())

    out = bytearray()
    for chunk in range(CHUNK_COUNT):
        pointer = struct.unpack(
            "<Q", read_at(blob, sections, POINTER_TABLE_VA + 8 * chunk, 8)
        )[0]
        cipher = read_at(blob, sections, pointer, CHUNK_SIZE)
        logger.info("chunk {} at VA {:#x}: {}", chunk, pointer, cipher.hex())
        for index, byte in enumerate(cipher):
            out.append(((byte + ((LAYER1_BIAS - LAYER1_STEP * index) & 0xFF)) & 0xFF) ^ keys[chunk])
    return bytes(out)


def decrypt_layer2(data: bytes) -> bytes:
    """Undo the 8-byte rolling key applied with a stride of 3."""
    key8 = struct.pack("<Q", LAYER2_KEY)
    logger.info("layer-2 key: {!r}", key8)
    return bytes(
        byte ^ key8[(LAYER2_OFFSET + LAYER2_STRIDE * index) & 7] for index, byte in enumerate(data)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path(__file__).with_name("TeaGod.exe"),
        help="path to the PE challenge binary",
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level: <7}</level> {message}")

    if not args.binary.is_file():
        logger.error("no such file: {}", args.binary)
        return 1

    blob = args.binary.read_bytes()
    logger.info("loaded {} ({} bytes)", args.binary.name, len(blob))

    image_base, sections = read_sections(blob)
    logger.info("image base {:#x}, sections: {}", image_base, ", ".join(s.name for s in sections))

    flag = decrypt_layer2(decrypt_layer1(blob, sections)).decode()
    logger.success("flag = {}", flag)
    if flag != EXPECTED_FLAG:
        logger.error("does not match the known-good flag")
        return 1
    logger.success("matches the known-good flag")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
