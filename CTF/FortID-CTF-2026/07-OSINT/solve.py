#!/usr/bin/env python3
"""Breaking News — offline part of the solve.

1. Read the commit dates of the leaked git repo (secret-key.zip) and draw them
   as a GitHub contribution graph (rows = weekdays from Sunday, columns =
   weeks). Every commit is at 12:00:00 UTC and there is one per day, so only
   the date carries information. The pixels spell the passphrase.
2. Decrypt the leaked why_i_did_what_i_did.png.enc with that passphrase using
   the author's own format (github.com/w4l73r-8l4ck-H4t/image-encryptor):
       IMGCRYPT | ver u8 | scrypt N,r,p u32be | salt_len,nonce_len u16be |
       salt | nonce | AES-256-GCM(ciphertext||tag), header used as AAD

    python3 solve.py <secret-key repo dir> [why_i_did_what_i_did.png.enc]
"""
from __future__ import annotations

import datetime as dt
import struct
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from loguru import logger

PASSPHRASE = "14m7h30neWh0Kn0ckzzz"   # read from the graph printed below
HEADER_FMT = ">8sBIIIHH"


def commit_dates(repo: Path) -> list[dt.date]:
    out = subprocess.run(["git", "-C", str(repo), "log", "--format=%ad", "--date=short"],
                         check=True, capture_output=True, text=True).stdout
    return sorted(dt.date.fromisoformat(line) for line in out.split())


def contribution_graph(dates: list[dt.date]) -> list[str]:
    start = dates[0] - dt.timedelta(days=(dates[0].weekday() + 1) % 7)   # back to Sunday
    weeks = (dates[-1] - start).days // 7 + 1
    days = set(dates)
    return ["".join("#" if start + dt.timedelta(days=7 * w + wd) in days else " "
                    for w in range(weeks)) for wd in range(7)]


def decrypt_container(blob: bytes, passphrase: str) -> bytes:
    hlen = struct.calcsize(HEADER_FMT)
    magic, version, n, r, p, salt_len, nonce_len = struct.unpack(HEADER_FMT, blob[:hlen])
    if magic != b"IMGCRYPT" or version != 1:
        raise ValueError("not an IMGCRYPT v1 container")
    salt = blob[hlen:hlen + salt_len]
    nonce = blob[hlen + salt_len:hlen + salt_len + nonce_len]
    key = Scrypt(salt=salt, length=32, n=n, r=r, p=p).derive(passphrase.encode())
    return AESGCM(key).decrypt(nonce, blob[hlen + salt_len + nonce_len:], blob[:hlen])


def main() -> None:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "secret-key")
    dates = commit_dates(repo)
    logger.info(f"{len(dates)} commits, {dates[0]} .. {dates[-1]}")
    rows = contribution_graph(dates)
    for start in range(0, len(rows[0]), 110):                  # print in readable slices
        print("\n".join(row[start:start + 110] for row in rows), end="\n\n")

    if len(sys.argv) > 2:
        enc = Path(sys.argv[2])
        png = decrypt_container(enc.read_bytes(), PASSPHRASE)   # GCM tag verifies the key
        out = enc.with_name(enc.name.removesuffix(".enc"))
        out.write_bytes(png)
        logger.success(f"decrypted {enc.name} -> {out.name} ({len(png)} bytes); the flag is in the image")


if __name__ == "__main__":
    main()
