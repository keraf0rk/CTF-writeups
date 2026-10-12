#!/usr/bin/env python3
"""Human RNG — solve / verify.

ciphertext = QR(flag) XOR last 1681 bits of a bitstream typed by a human.
The typed prefix (1999 bits) is public. Humans are bad RNGs: the prefix flips
bits ~70% of the time and rarely repeats a bit more than 3 times. An order-4
Markov model trained on the prefix therefore tells a "human" keystream apart
from a random one.

For a candidate flag:  key = ciphertext XOR QR(candidate).
The right flag yields a key that looks like the prefix (log-likelihood per bit
~ -0.58); any wrong part of the flag turns the matching QR modules into noise
(~ -0.80 per bit). QR v6-H stores data in 4 Reed-Solomon blocks, so every
block can be scored on its own and pinpoints which part of the text is wrong.

    python3 solve.py <handout_dir> [candidate_flag]
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import qrcode
from loguru import logger
from PIL import Image
from qrcode.base import rs_blocks
from qrcode.constants import ERROR_CORRECT_H

SIZE, ORDER = 41, 4
FLAG = "FortID{humans_are_not_good_random_number_generators}"


def qr_bits(text: str) -> np.ndarray:
    qr = qrcode.QRCode(version=6, error_correction=ERROR_CORRECT_H,
                       box_size=1, border=0, mask_pattern=0)
    qr.add_data(text)
    qr.make(fit=False)
    return np.array([1 if m else 0 for row in qr.get_matrix() for m in row], dtype=np.uint8)


def load_ciphertext(png: Path) -> np.ndarray:
    """ciphertext.png is the 41x41 grid scaled x10; black = 1."""
    img = Image.open(png).convert("L")
    cell = img.width // SIZE
    px = np.asarray(img)[cell // 2::cell, cell // 2::cell][:SIZE, :SIZE]
    return (px < 128).astype(np.uint8).ravel()


class MarkovModel:
    """Order-k bit predictor trained on the known human-typed prefix."""

    def __init__(self, prefix: list[int], order: int = ORDER) -> None:
        self.order = order
        ones, total = Counter(), Counter()
        for i in range(order, len(prefix)):
            ctx = tuple(prefix[i - order:i])
            total[ctx] += 1
            ones[ctx] += prefix[i]
        self.p1 = {c: (ones[c] + 1) / (total[c] + 2) for c in total}

    def bit_logprobs(self, bits: np.ndarray) -> np.ndarray:
        out = np.zeros(len(bits))
        for i in range(self.order, len(bits)):
            p = self.p1.get(tuple(bits[i - self.order:i]), 0.5)
            out[i] = math.log(p if bits[i] else 1 - p)
        return out[self.order:]


def module_block_map() -> np.ndarray:
    """For every data module of QR v6-H, the Reed-Solomon block it belongs to (-1 = function)."""
    qr = qrcode.QRCode(version=6, error_correction=ERROR_CORRECT_H, box_size=1, border=0, mask_pattern=0)
    qr.add_data("x"); qr.make(fit=False)
    blocks = rs_blocks(6, ERROR_CORRECT_H)
    order: list[int] = []                          # interleaved codeword -> block
    max_d = max(b.data_count for b in blocks)
    max_e = max(b.total_count - b.data_count for b in blocks)
    for i in range(max_d):
        order += [bi for bi, b in enumerate(blocks) if i < b.data_count]
    for i in range(max_e):
        order += [bi for bi, b in enumerate(blocks) if i < b.total_count - b.data_count]
    qr.modules = [[None] * SIZE for _ in range(SIZE)]   # re-run the placement walk
    qr.setup_position_probe_pattern(0, 0)
    qr.setup_position_probe_pattern(SIZE - 7, 0)
    qr.setup_position_probe_pattern(0, SIZE - 7)
    qr.setup_position_adjust_pattern(); qr.setup_timing_pattern(); qr.setup_type_info(False, 0)
    positions, inc, row, col = [], -1, SIZE - 1, SIZE - 1
    while col > 0:
        if col <= 6:
            col -= 1
        while True:
            for c in range(2):
                if qr.modules[row][col - c] is None:
                    positions.append(row * SIZE + col - c)
            row += inc
            if row < 0 or row >= SIZE:
                row -= inc; inc = -inc; break
        col -= 2
    owner = np.full(SIZE * SIZE, -1)
    for k, pos in enumerate(positions):
        if k // 8 < len(order):
            owner[pos] = order[k // 8]
    return owner


def main() -> None:
    handout = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    candidate = sys.argv[2] if len(sys.argv) > 2 else FLAG

    raw = (handout / "bitstream.txt").read_text()
    prefix = [int(c) for c in raw.split("<")[0] if c in "01"]
    model = MarkovModel(prefix)
    ct = load_ciphertext(handout / "ciphertext.png")

    ref = model.bit_logprobs(np.array(prefix, dtype=np.uint8)).mean()
    rng = np.random.default_rng(0)
    noise = model.bit_logprobs(rng.integers(0, 2, SIZE * SIZE, dtype=np.uint8)).mean()
    logger.info(f"prefix: {len(prefix)} bits, flip rate {np.mean(np.diff(prefix) != 0):.3f}")
    logger.info(f"reference LL/bit: human prefix {ref:.3f} | random noise {noise:.3f}")

    key = ct ^ qr_bits(candidate)
    lp = model.bit_logprobs(key)
    owner = module_block_map()[ORDER:]
    logger.info(f"candidate {candidate}")
    logger.info(f"  whole key LL/bit {lp.mean():.3f}")
    ok = True
    for b in range(4):
        score = lp[owner == b].mean()
        verdict = "human-like" if score > (ref + noise) / 2 else "NOISE -> wrong text in this block"
        ok &= score > (ref + noise) / 2
        logger.info(f"  RS block {b}: LL/bit {score:.3f}  {verdict}")
    (logger.success if ok else logger.error)(
        f"FLAG: {candidate}" if ok else "candidate rejected")


if __name__ == "__main__":
    main()
