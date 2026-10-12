#!/usr/bin/env python3
"""Catch Me If You Can — solve.

The "flag button" runs away from the cursor, but the flag is never fetched from
a server: the click handler holds it client-side as three string fragments,
joins them, reverses the string and Base64-decodes it. Reproduce that offline.
"""
from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

from loguru import logger


def extract_fragments(html: str) -> list[str]:
    block = re.search(r"const scrambled = \[(.*?)\]\.join", html, re.S)
    if block is None:
        raise ValueError("scrambled array not found")
    return re.findall(r'"([^"]*)"', block.group(1))


def main() -> None:
    html = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html").read_text()
    scrambled = "".join(extract_fragments(html))
    flag = base64.b64decode(scrambled[::-1]).decode()   # atob([...s].reverse().join(""))
    logger.success(f"FLAG: {flag}")


if __name__ == "__main__":
    main()
