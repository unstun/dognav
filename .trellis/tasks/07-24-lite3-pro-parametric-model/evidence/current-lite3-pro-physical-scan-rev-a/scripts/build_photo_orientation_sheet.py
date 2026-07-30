#!/usr/bin/env python3
"""Create an indexed contact sheet without modifying the source photographs."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    paths = sorted(args.source.glob("photo-*.jpg"))
    cell_w, cell_h = 520, 440
    columns = 2
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (cell_w * columns, cell_h * rows), (238, 241, 244))
    font = ImageFont.load_default(size=20)
    for index, path in enumerate(paths):
        image = ImageOps.exif_transpose(Image.open(path).convert("RGB"))
        image.thumbnail((cell_w - 24, cell_h - 54))
        x0 = (index % columns) * cell_w
        y0 = (index // columns) * cell_h
        x = x0 + (cell_w - image.width) // 2
        y = y0 + 42 + (cell_h - 48 - image.height) // 2
        sheet.paste(image, (x, y))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((x0, y0, x0 + cell_w, y0 + 36), fill=(25, 31, 39))
        draw.text((x0 + 12, y0 + 8), f"{path.name} — stored pixels / EXIF-transposed", fill="white", font=font)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)


if __name__ == "__main__":
    main()
