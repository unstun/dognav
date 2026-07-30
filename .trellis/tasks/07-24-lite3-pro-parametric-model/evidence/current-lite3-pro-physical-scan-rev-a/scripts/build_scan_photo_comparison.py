#!/usr/bin/env python3
"""Build a visual audit that the scan and corrected photo share one heading."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def panel(source: Path, title: str, width: int, height: int) -> Image.Image:
    image = Image.open(source).convert("RGB")
    fitted = ImageOps.contain(image, (width - 40, height - 120))
    result = Image.new("RGB", (width, height), (248, 249, 250))
    result.paste(fitted, ((width - fitted.width) // 2, 70 + (height - 120 - fitted.height) // 2))
    draw = ImageDraw.Draw(result)
    draw.rectangle((0, 0, width, 56), fill=(25, 31, 39))
    draw.text((20, 16), title, fill="white", font=ImageFont.load_default(size=24))
    draw.line((width * 0.56, height - 36, width * 0.88, height - 36), fill=(0, 103, 190), width=8)
    draw.polygon(
        [(width * 0.88, height - 36), (width * 0.84, height - 54), (width * 0.84, height - 18)],
        fill=(0, 103, 190),
    )
    draw.text((width * 0.62, height - 68), "+X FRONT", fill=(0, 82, 155), font=ImageFont.load_default(size=20))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scan", type=Path)
    parser.add_argument("photo", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    left = panel(args.scan, "ORIENTED 3D SCAN — orthographic top", 1000, 850)
    right = panel(args.photo, "ROTATED PHOTO — perspective remains", 1000, 850)
    result = Image.new("RGB", (2000, 850), "white")
    result.paste(left, (0, 0))
    result.paste(right, (1000, 0))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output)


if __name__ == "__main__":
    main()
