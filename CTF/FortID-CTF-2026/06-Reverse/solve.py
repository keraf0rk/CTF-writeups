#!/usr/bin/env python3
"""Paint me a Flag — solve.

Renders every flag_part_NN.pmaf with the fast bit-exact renderer (render.c),
starting from the matching flag_part_NN.png, and stacks the results.

    cc -O2 -o render render.c
    python3 solve.py <handout_dir> [out_dir]
"""
from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from loguru import logger
from PIL import Image

RENDER = Path(__file__).with_name("render")


def png_to_rgb32(png: Path, raw: Path) -> tuple[int, int]:
    """Pack the starting canvas as little-endian uint32 0x00RRGGBB."""
    img = np.asarray(Image.open(png).convert("RGB"), dtype=np.uint32)
    packed = (img[..., 0] << 16) | (img[..., 1] << 8) | img[..., 2]
    raw.write_bytes(packed.astype("<u4").tobytes())
    return img.shape[1], img.shape[0]


def rgb32_to_image(raw: Path, width: int, height: int) -> Image.Image:
    packed = np.frombuffer(raw.read_bytes(), dtype="<u4").reshape(height, width)
    rgb = np.stack([(packed >> 16) & 255, (packed >> 8) & 255, packed & 255], axis=-1)
    return Image.fromarray(rgb.astype(np.uint8), "RGB")


def render_part(pmaf: Path, out_dir: Path) -> Path:
    part = pmaf.stem.removeprefix("flag_part_")
    start_raw, end_raw = out_dir / f"start_{part}.rgb32", out_dir / f"end_{part}.rgb32"
    width, height = png_to_rgb32(pmaf.with_suffix(".png"), start_raw)
    subprocess.run([str(RENDER), str(pmaf), str(start_raw), str(end_raw)], check=True)
    out_png = out_dir / f"out_{part}.png"
    rgb32_to_image(end_raw, width, height).save(out_png)
    start_raw.unlink(); end_raw.unlink()
    logger.success(f"part {part} rendered -> {out_png.name}")
    return out_png


def stack(parts: list[Path], target: Path, height: int = 120) -> None:
    """Scale every part to the same height and lay them out in one row."""
    imgs = [Image.open(p) for p in parts]
    imgs = [im.resize((max(1, im.width * height // im.height), height)) for im in imgs]
    sheet = Image.new("RGB", (sum(im.width for im in imgs), height), "white")
    x = 0
    for im in imgs:
        sheet.paste(im, (x, 0)); x += im.width
    sheet.save(target)
    logger.success(f"flag sheet -> {target}")


def main() -> None:
    handout = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "out")
    out_dir.mkdir(exist_ok=True)
    parts = sorted(handout.glob("flag_part_*.pmaf"))
    with ThreadPoolExecutor() as pool:
        rendered = list(pool.map(lambda p: render_part(p, out_dir), parts))
    stack(rendered, out_dir / "flag.png")


if __name__ == "__main__":
    main()
