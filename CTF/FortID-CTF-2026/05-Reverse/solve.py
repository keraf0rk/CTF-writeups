#!/usr/bin/env python3
"""Meteor Shower (NES ROM) — solve.

Static analysis of the 6502 code (NROM, PRG at $8000):
  * $80EF  — while the game is not won, every newly pressed A appends bit 0 and
             every newly pressed B appends bit 1 to a buffer at $0400.
  * $8158  — once 95 bits are collected, bit i must equal
             (T1[k] ^ T2[k] ^ i) & 1,  k = 0x0B, then k = (k + 0x25) & 0x7F,
             where T1 = $8718 and T2 = $8798 — the same tables that spawn the
             meteors (x position / speed). All 95 matches -> state 4.
  * state 4 -> screen 5 ($8577): "EASTER EGG FOUND ... I HOPE YOU LIKE
             BACON & EGGS!!! FIVE STRIPS AT A TIME!"  -> Bacon cipher, 5 bits/letter.
"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

PRG_BASE, T1_ADDR, T2_ADDR = 0x8000, 0x8718, 0x8798
BITS, K0, STEP = 0x5F, 0x0B, 0x25


def load_prg(path: Path) -> bytes:
    rom = path.read_bytes()
    assert rom[:4] == b"NES\x1a", "not an iNES ROM"
    prg_banks = rom[4]
    return rom[16:16 + 16384 * prg_banks]


def screen_text(prg: bytes, addr: int) -> str:
    """On-screen strings: 0x80.. = 'A'.., 0x00 = space, 0xFF terminates."""
    out, i = [], addr - PRG_BASE
    while prg[i] != 0xFF:
        c = prg[i]
        out.append(" " if c == 0 else chr(c - 0x80 + 65) if 0x80 <= c <= 0x99 else "·")
        i += 1
    return "".join(out)


def secret_bits(prg: bytes) -> list[int]:
    t1 = prg[T1_ADDR - PRG_BASE:T1_ADDR - PRG_BASE + 128]
    t2 = prg[T2_ADDR - PRG_BASE:T2_ADDR - PRG_BASE + 128]
    bits, k = [], K0
    for i in range(BITS):
        bits.append((t1[k] ^ t2[k] ^ i) & 1)
        k = (k + STEP) & 0x7F
    return bits


def bacon_decode(bits: list[int]) -> str:
    groups = ["".join(map(str, bits[i:i + 5])) for i in range(0, len(bits), 5)]
    return "".join(chr(65 + int(g, 2)) for g in groups)   # 26-letter Bacon: A=00000 ... Z=11001


def main() -> None:
    prg = load_prg(Path(sys.argv[1] if len(sys.argv) > 1 else "meteor_shower.nes"))
    for addr in (0x86AA, 0x86BC, 0x86D1, 0x86E1, 0x86F1, 0x8701):
        logger.info(f"win screen ${addr:04X}: {screen_text(prg, addr)}")
    bits = secret_bits(prg)
    logger.info("button sequence: " + "".join("AB"[b] for b in bits))
    plain = bacon_decode(bits)
    logger.info(f"Bacon plaintext: {plain}")
    logger.success("FLAG: FortID{SCIENTIA_POTENTIA_EST}")


if __name__ == "__main__":
    main()
