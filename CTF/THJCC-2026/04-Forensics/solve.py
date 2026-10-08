#!/usr/bin/env python3
"""THJCC 2026 Summer — "Welcome" solver.

The challenge ships a single 800x600 GIF. Each of its 57 frames renders exactly
one character of a string. Reading the frames left to right gives a *lossy*
transcription, because the encoder emitted only one frame per visible glyph:
runs of two identical characters ("tt", "//", "uu", "ss") collapsed into one.

The missing information lives in the Graphic Control Extension of every frame:
ordinary characters are shown for 50 ms, the four collapsed ones for 100 ms.
Doubling every long-delay glyph restores the original string.

Usage:
    python3 solve.py --gif welcome.gif --dump-frames out/
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from loguru import logger
from PIL import Image

# Glyph rendered by each frame, in frame order, transcribed by eye from the
# contact sheet produced by --dump-frames. 57 characters for 57 frames.
GLYPHS: str = "htps:/welcome.xzhiyou.idv.tw;Pas_code:NT9C-S8DP-D85B-Z8H6"

EXPECTED_PLAINTEXT: str = (
    "https://welcome.xzhiyouu.idv.tw;Pass_code:NT9C-S8DP-D85B-Z8H6"
)


def load_frame_durations(gif_path: Path) -> list[int]:
    """Return the per-frame delay in milliseconds, in frame order."""
    durations: list[int] = []
    with Image.open(gif_path) as img:
        for index in range(img.n_frames):
            img.seek(index)
            duration = img.info.get("duration")
            if duration is None:
                raise ValueError(f"frame {index} carries no duration")
            durations.append(int(duration))
    logger.info("read {} frame durations from {}", len(durations), gif_path.name)
    return durations


def dump_frames(gif_path: Path, out_dir: Path) -> Path:
    """Write every coalesced frame as PNG plus a contact sheet; return the sheet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    thumbs: list[Image.Image] = []
    with Image.open(gif_path) as img:
        for index in range(img.n_frames):
            img.seek(index)
            frame = img.convert("RGB")
            frame.save(out_dir / f"frame_{index:02d}.png")
            thumbs.append(frame.resize((100, 75)))

    columns = 8
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 100, rows * 75), "black")
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % columns) * 100, (index // columns) * 75))

    sheet_path = out_dir / "contact_sheet.png"
    sheet.save(sheet_path)
    logger.info("wrote {} frames and {}", len(thumbs), sheet_path)
    return sheet_path


def find_long_delay(durations: list[int]) -> int:
    """Return the delay value that marks a doubled glyph.

    The GIF uses exactly two delays: the common one for single characters and a
    rarer, longer one for characters that appear twice in a row.
    """
    histogram = Counter(durations)
    if len(histogram) != 2:
        raise ValueError(f"expected exactly two distinct delays, got {dict(histogram)}")
    base, long_delay = sorted(histogram)
    logger.info(
        "delays: {} ms x{} (single), {} ms x{} (doubled)",
        base,
        histogram[base],
        long_delay,
        histogram[long_delay],
    )
    return long_delay


def reconstruct(glyphs: str, durations: list[int]) -> str:
    """Expand every long-delay glyph into two characters."""
    if len(glyphs) != len(durations):
        raise ValueError(
            f"{len(glyphs)} glyphs vs {len(durations)} frames — transcription is off"
        )
    long_delay = find_long_delay(durations)
    pieces: list[str] = []
    for glyph, duration in zip(glyphs, durations, strict=True):
        repeat = 2 if duration == long_delay else 1
        if repeat == 2:
            logger.debug("doubling {!r} (delay {} ms)", glyph, duration)
        pieces.append(glyph * repeat)
    return "".join(pieces)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gif",
        type=Path,
        default=Path(__file__).with_name("welcome.gif"),
        help="path to welcome.gif",
    )
    parser.add_argument(
        "--dump-frames",
        type=Path,
        default=None,
        metavar="DIR",
        help="also write every frame as PNG plus a contact sheet into DIR",
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level: <7}</level> {message}")

    if not args.gif.is_file():
        logger.error("no such file: {}", args.gif)
        return 1

    if args.dump_frames is not None:
        dump_frames(args.gif, args.dump_frames)

    durations = load_frame_durations(args.gif)
    plaintext = reconstruct(GLYPHS, durations)

    logger.info("frames as read : {}", GLYPHS)
    logger.info("reconstructed  : {}", plaintext)

    url, _, credential = plaintext.partition(";")
    logger.success("url       = {}", url)
    logger.success("pass code = {}", credential.removeprefix("Pass_code:"))

    if plaintext != EXPECTED_PLAINTEXT:
        logger.error("does not match the known-good plaintext")
        return 1
    logger.success("matches the known-good plaintext")
    logger.info("open the url, submit the pass code, follow the pastebin link")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
