#!/usr/bin/env python3
"""T9 flag checker (chall.pyc, CPython 3.10) — solve.

The checker:
  1. len(flag) == 81, flag = "FortID{" + body + "}"
  2. every "_"-separated word is all-lowercase letters or all-digits
  3. t9.get_touchtone("-".join(words))[::-1] == TARGET   (keypad digits, reversed)
  4. sha256(flag) == DIGEST

So: reverse TARGET, split on "-", read each group as a word typed on a phone
keypad (digit groups stay digits), and confirm with the SHA-256 from the
bytecode. Each group reads as exactly one English word here.
"""
from __future__ import annotations

import hashlib

from loguru import logger

TARGET = "33696-7383-3824-4-9465664238-36-32347-878267-8766-348-55487-74-0133-24566"
DIGEST = "3576c495f89236515fbbfbfb519dceb9899122e92460d418d2ce37a1ff357e0c"

KEYPAD = {d: letters for d, letters in
          {"2": "abc", "3": "def", "4": "ghi", "5": "jkl",
           "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"}.items()}
TO_DIGIT = {ch: d for d, letters in KEYPAD.items() for ch in letters}

# keypad groups (after reversing TARGET) and the word each one spells
WORDS = ["nokia", "3310", "is", "still", "the", "most", "robust", "piece",
         "of", "technology", "i", "have", "ever", "owned"]


def touchtone(word: str) -> str:
    return "".join(TO_DIGIT.get(ch, ch) for ch in word)


def main() -> None:
    groups = TARGET[::-1].split("-")
    logger.info(f"keypad groups: {groups}")
    for group, word in zip(groups, WORDS, strict=True):
        assert touchtone(word) == group, (word, group)
        logger.info(f"  {group:>12} -> {word}")
    flag = "FortID{" + "_".join(WORDS) + "}"
    assert len(flag) == 81
    assert hashlib.sha256(flag.encode()).hexdigest() == DIGEST
    logger.success(f"FLAG: {flag}  (length 81, SHA-256 matches)")


if __name__ == "__main__":
    main()
