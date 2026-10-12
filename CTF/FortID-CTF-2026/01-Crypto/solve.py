#!/usr/bin/env python3
"""Hic Sunt Dracones — solve.

Koblitz encoding puts every character in the clear inside the x coordinate:
    x = ord(ch) * 20 + j,  j in [1, 19]   ->   ch = (x - 1) // 20
The "dragon curve" cipher only translates each point by size * u_i with an
integer vector u_i. Because the turtle heading is never reset, even points are
shifted along Y (x untouched) and odd points along X by +/-C, C = size * 128.

A single known plaintext character at an odd position pins C to a 19-wide
window; intersecting the windows of the known prefix "FortID{" and requiring
C % 128 == 0 leaves exactly one C.
"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

KNOWN_PREFIX = "FortID{"


def parse_x(output: str) -> list[int]:
    """output.txt is 'X<x0>X<x1>...XY<y0>Y<y1>...'; only x matters."""
    xs_part = output.strip().split("XY")[0]
    return [int(v) for v in xs_part.split("X")[1:]]


def shift_window(x: int, ch: str) -> tuple[int, int]:
    """Range of C such that x -/+ C encodes `ch` (x0 in [20*ord+1, 20*ord+19])."""
    x0_lo, x0_hi = 20 * ord(ch) + 1, 20 * ord(ch) + 19
    return (x - x0_hi, x - x0_lo) if x > 0 else (-x + x0_lo, -x + x0_hi)


def recover_shift(xs: list[int]) -> int:
    lo, hi = 0, 1 << 512
    for i, ch in enumerate(KNOWN_PREFIX):
        if i % 2 == 1:                      # odd points carry the X shift
            a, b = shift_window(xs[i], ch)
            lo, hi = max(lo, a), min(hi, b)
    candidates = [c for c in range(lo, hi + 1) if c % 128 == 0]
    if len(candidates) != 1:
        raise ValueError(f"expected one shift, got {candidates}")
    return candidates[0]


def decode(xs: list[int], shift: int) -> str:
    chars = []
    for i, x in enumerate(xs):
        x0 = x if i % 2 == 0 else (x - shift if x > 0 else x + shift)
        chars.append(chr((x0 - 1) // 20))
    return "".join(chars)


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "output.txt")
    xs = parse_x(path.read_text())
    shift = recover_shift(xs)
    logger.info(f"points: {len(xs)}, shift C = {shift} (size = C / 128 = {shift // 128})")
    logger.success(f"FLAG: {decode(xs, shift)}")


if __name__ == "__main__":
    main()
