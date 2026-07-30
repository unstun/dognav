#!/usr/bin/env python3
"""Create non-destructive, consistently oriented photo copies.

All whole-robot top views are rotated so the Lite3 nose/front points right,
matching the scan's +X screen direction. Rotation does not claim perspective
rectification; the corrected copies remain qualitative evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


# Pillow angles are counter-clockwise. These values were visually checked
# against the rounded nose and the compute-enclosure position.
ROTATIONS_DEG = {
    "photo-01.jpg": 180,
    "photo-02.jpg": 180,
    "photo-03.jpg": 180,
    "photo-04.jpg": 0,
    "photo-05.jpg": 180,
    "photo-06.jpg": 180,
    "photo-07.jpg": 180,
    "photo-08.jpg": 180,
    "photo-09.jpg": 0,
    "photo-10.jpg": 90,
}


def contact_sheet(paths: list[Path], output: Path) -> None:
    cell_w, cell_h, columns = 640, 480, 2
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (cell_w * columns, cell_h * rows), (238, 241, 244))
    font = ImageFont.load_default(size=20)
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((cell_w - 24, cell_h - 54))
        x0, y0 = (index % columns) * cell_w, (index // columns) * cell_h
        x = x0 + (cell_w - image.width) // 2
        y = y0 + 42 + (cell_h - 48 - image.height) // 2
        sheet.paste(image, (x, y))
        draw.rectangle((x0, y0, x0 + cell_w, y0 + 36), fill=(25, 31, 39))
        draw.text((x0 + 12, y0 + 8), f"{path.name} — orientation only; front -> right", fill="white", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    outputs = []
    for name, angle in ROTATIONS_DEG.items():
        source = args.source / name
        image = ImageOps.exif_transpose(Image.open(source).convert("RGB"))
        corrected = image.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        destination = args.output / name
        corrected.save(destination, quality=94, subsampling=0)
        outputs.append(destination)
        records.append(
            {
                "source": str(source),
                "output": str(destination),
                "counter_clockwise_rotation_deg": angle,
                "perspective_rectified": False,
                "measurement_claim": "qualitative orientation reference only",
            }
        )
    (args.output / "orientation-manifest.json").write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    contact_sheet(outputs, args.output / "00-standardized-photo-contact-sheet.png")


if __name__ == "__main__":
    main()
