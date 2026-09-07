#!/usr/bin/env python3
"""Solve script for TFC CTF — "MATH OR METH?" (Crypto).

Recovers the flag hidden as one row of a small-entry matrix whose secret
mod-p linear combination is published. Uses an orthogonal lattice attack
(Nguyen-Stern style) followed by a Fincke-Pohst CVP enumeration to pull the
non-negative rows out of the recovered lattice.

Deps: fpylll, pycryptodome, loguru, numpy.
    pip install fpylll pycryptodome loguru numpy --break-system-packages
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import math
import numpy as np
from fpylll import BKZ, LLL, IntegerMatrix
from Crypto.Util.number import long_to_bytes
from loguru import logger

CHALLENGE_OUTPUT = Path(__file__).with_name("output.py")


def load_output(path: Path) -> tuple[int, int, int, int, list[int]]:
    """Load n, m, B, p, h from the challenge's output.py (plain assignments)."""
    namespace: dict[str, object] = {}
    exec(path.read_text(), namespace)  # noqa: S102 - trusted local challenge file
    n, m, b, p, h = (namespace[k] for k in ("n", "m", "B", "p", "h"))
    assert isinstance(h, list) and len(h) == m
    return int(n), int(m), int(b), int(p), [int(x) for x in h]


def _matrix(rows: list[list[int]]) -> IntegerMatrix:
    mat = IntegerMatrix(len(rows), len(rows[0]))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            mat[i, j] = int(value)
    return mat


def _rows(mat: IntegerMatrix) -> list[list[int]]:
    return [[mat[i, j] for j in range(mat.ncols)] for i in range(mat.nrows)]


def orthogonal_lattice(h: list[int], p: int) -> list[list[int]]:
    """Basis of Lambda = { u in Z^m : <u, h> == 0 (mod p) }."""
    m = len(h)
    h0_inv = pow(h[0], -1, p)
    rows: list[list[int]] = []
    for j in range(1, m):
        row = [0] * m
        row[j] = 1
        row[0] = (-h0_inv * h[j]) % p
        rows.append(row)
    origin = [0] * m
    origin[0] = p
    rows.append(origin)
    return rows


def recover_row_lattice(h: list[int], p: int, n: int) -> list[list[int]]:
    """Recover a basis of L_A (integer span of the small matrix rows)."""
    m = len(h)

    lam = _matrix(orthogonal_lattice(h, p))
    LLL.reduction(lam)
    reduced = _rows(lam)
    by_norm = sorted(reduced, key=lambda v: sum(x * x for x in v))
    perp = by_norm[: m - n]  # the m-n genuinely short vectors span L_A^perp
    logger.info("recovered L_A^perp: {} short vectors", len(perp))

    scale = 1 << 60
    embed: list[list[int]] = []
    for i in range(m):
        row = [0] * (m + len(perp))
        row[i] = 1
        for t, w in enumerate(perp):
            row[m + t] = scale * w[i]
        embed.append(row)
    emb = _matrix(embed)
    LLL.reduction(emb)
    la = [row[:m] for row in _rows(emb) if all(v == 0 for v in row[m:])]
    assert len(la) == n, f"expected rank {n}, got {len(la)}"
    logger.info("recovered L_A: rank {}", len(la))
    return la


def box_lattice_points(basis: list[list[int]], base: int, radius: float) -> Iterator[list[int]]:
    """Enumerate lattice points inside [0, base)^m near the box centre.

    Fincke-Pohst CVP enumeration around t = (base-1)/2 in every coordinate;
    the matrix rows all live inside that box, so a tight radius finds them.
    """
    mat = _matrix(basis)
    LLL.reduction(mat)
    BKZ.reduction(mat, BKZ.Param(block_size=20))
    b = np.array(_rows(mat), dtype=float)
    dim, m = b.shape

    mu = np.zeros((dim, dim))
    bstar = np.zeros((dim, m))
    norms = np.zeros(dim)
    for i in range(dim):
        bstar[i] = b[i]
        for j in range(i):
            mu[i, j] = np.dot(b[i], bstar[j]) / norms[j]
            bstar[i] -= mu[i, j] * bstar[j]
        norms[i] = np.dot(bstar[i], bstar[i])

    target = np.full(m, (base - 1) / 2.0)
    tau = np.array([np.dot(target, bstar[i]) / norms[i] for i in range(dim)])
    coeffs = [0] * dim
    radius_sq = radius * radius

    def walk(i: int, partial: float) -> Iterator[list[int]]:
        if i < 0:
            vec = np.zeros(m)
            for k in range(dim):
                vec += coeffs[k] * b[k]
            rounded = [int(round(x)) for x in vec]
            if all(0 <= x < base for x in rounded):
                yield rounded
            return
        centre = tau[i] - sum(mu[j, i] * coeffs[j] for j in range(i + 1, dim))
        remaining = radius_sq - partial
        if remaining < 0:
            return
        width = math.sqrt(remaining / norms[i])
        for xi in range(math.ceil(centre - width), math.floor(centre + width) + 1):
            coeffs[i] = xi
            yield from walk(i - 1, partial + (xi - centre) ** 2 * norms[i])
        coeffs[i] = 0

    yield from walk(dim - 1, 0.0)


def decode_row(digits: list[int], base: int) -> bytes:
    value = 0
    for digit in reversed(digits):
        value = value * base + digit
    return long_to_bytes(value)


def solve(path: Path = CHALLENGE_OUTPUT) -> str:
    n, m, b, p, h = load_output(path)
    base = b + 1
    logger.info("n={} m={} base={} p_bits={}", n, m, base, p.bit_length())

    la = recover_row_lattice(h, p, n)

    seen: set[tuple[int, ...]] = set()
    for row in box_lattice_points(la, base, radius=140.0):
        key = tuple(row)
        if key in seen:
            continue
        seen.add(key)
        data = decode_row(row, base)
        if b"TFCCTF{" in data:  # flag embedded whole
            flag = data[data.index(b"TFCCTF{"):].split(b"}")[0].decode() + "}"
            logger.success("flag: {}", flag)
            return flag
        # the planted row decodes to the message placed inside TFCCTF{...}
        if len(data) >= 20 and all(32 <= c < 127 for c in data):
            flag = "TFCCTF{" + data.decode() + "}"
            logger.success("recovered message row -> {}", flag)
            return flag
    raise RuntimeError("flag not found")


if __name__ == "__main__":
    print(solve())
