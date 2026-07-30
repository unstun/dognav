#!/usr/bin/env python3
"""Render scan-derived top-mount reference views on a fixed millimetre grid."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from glb_scan import GlbDocument, combined_cloud
from orient_lite3_scan import fit_orientation, roi_mask, transform_to_standard


def _visible_samples(
    points: np.ndarray,
    colors: np.ndarray,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    z_range: tuple[float, float],
    width: int,
    height: int,
    margin: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    mask = (
        (points[:, 0] >= x_range[0])
        & (points[:, 0] <= x_range[1])
        & (points[:, 1] >= y_range[0])
        & (points[:, 1] <= y_range[1])
        & (points[:, 2] >= z_range[0])
        & (points[:, 2] <= z_range[1])
    )
    selected = points[mask]
    rgb = colors[mask]
    scale = min((width - 2 * margin) / (x_range[1] - x_range[0]), (height - 2 * margin) / (y_range[1] - y_range[0]))
    left = (width - (x_range[1] - x_range[0]) * scale) / 2
    top = (height - (y_range[1] - y_range[0]) * scale) / 2
    px = np.rint(left + (selected[:, 0] - x_range[0]) * scale).astype(np.int32)
    py = np.rint(top + (y_range[1] - selected[:, 1]) * scale).astype(np.int32)
    linear = py.astype(np.int64) * width + px
    order = np.lexsort((-selected[:, 2], linear))
    sorted_linear = linear[order]
    first = np.r_[True, sorted_linear[1:] != sorted_linear[:-1]]
    chosen = order[first]
    transform = {"scale": scale, "left": left, "top": top, "x_range": x_range, "y_range": y_range}
    return px[chosen], py[chosen], selected[chosen, 2], rgb[chosen], transform


def _xy_to_pixel(x: float, y: float, transform: dict) -> tuple[float, float]:
    scale = transform["scale"]
    x_range = transform["x_range"]
    y_range = transform["y_range"]
    return (
        transform["left"] + (x - x_range[0]) * scale,
        transform["top"] + (y_range[1] - y) * scale,
    )


def render(
    points: np.ndarray,
    colors: np.ndarray,
    output: Path,
    title: str,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    z_range: tuple[float, float],
    grid_mm: float,
    height_mode: bool = False,
) -> None:
    width, height, margin = 1800, 1400, 130
    px, py, z, rgb, transform = _visible_samples(points, colors, x_range, y_range, z_range, width, height, margin)
    canvas = np.full((height, width, 3), 250, dtype=np.uint8)
    if height_mode:
        t = np.clip((z - z_range[0]) / (z_range[1] - z_range[0]), 0.0, 1.0)
        stops = np.array([0.0, 0.25, 0.55, 0.8, 1.0])
        palette = np.array([[37, 65, 118], [38, 139, 176], [60, 186, 142], [240, 198, 67], [194, 45, 45]])
        rgb = np.column_stack([np.interp(t, stops, palette[:, channel]) for channel in range(3)]).astype(np.uint8)
    for dy, dx in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        xx, yy = px + dx, py + dy
        inside = (xx >= 0) & (xx < width) & (yy >= 0) & (yy < height)
        canvas[yy[inside], xx[inside]] = rgb[inside]
    image = Image.fromarray(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    font = ImageFont.load_default(size=20)
    small = ImageFont.load_default(size=17)
    for x in np.arange(np.ceil(x_range[0] / grid_mm) * grid_mm, x_range[1] + 0.1, grid_mm):
        xx, _ = _xy_to_pixel(x, 0, transform)
        draw.line((xx, transform["top"], xx, transform["top"] + (y_range[1] - y_range[0]) * transform["scale"]), fill=(23, 38, 54, 70), width=1)
        draw.text((xx + 3, height - margin + 10), f"{x:.0f}", fill=(25, 31, 39, 255), font=small)
    for y in np.arange(np.ceil(y_range[0] / grid_mm) * grid_mm, y_range[1] + 0.1, grid_mm):
        _, yy = _xy_to_pixel(0, y, transform)
        draw.line((transform["left"], yy, transform["left"] + (x_range[1] - x_range[0]) * transform["scale"], yy), fill=(23, 38, 54, 70), width=1)
        draw.text((transform["left"] - 54, yy - 9), f"{y:.0f}", fill=(25, 31, 39, 255), font=small)
    # Reference axes through the compute-enclosure centre, the current X/Y origin.
    x0, y0 = _xy_to_pixel(0, 0, transform)
    draw.line((x0, transform["top"], x0, transform["top"] + (y_range[1] - y_range[0]) * transform["scale"]), fill=(0, 103, 190, 160), width=3)
    draw.line((transform["left"], y0, transform["left"] + (x_range[1] - x_range[0]) * transform["scale"], y0), fill=(0, 103, 190, 160), width=3)
    draw.rectangle((0, 0, width, 72), fill=(25, 31, 39, 255))
    draw.text((24, 20), title, fill="white", font=ImageFont.load_default(size=26))
    draw.text((24, height - 42), f"fixed orthographic grid = {grid_mm:.0f} mm; +X/front is right; +Y/left is up", fill=(25, 31, 39, 255), font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    document = GlbDocument.load(args.input)
    raw, colors, _clouds = combined_cloud(document)
    fit = fit_orientation(raw)
    local = roi_mask(raw)
    floor = float(np.percentile(raw[local, 1], 1.0))
    points = transform_to_standard(raw, fit, floor)
    render(
        points,
        colors,
        args.output_dir / "01-upper-body-metric-top.png",
        "Current Lite3 Professional scan — upper-body orthographic reference",
        (-280.0, 300.0),
        (-190.0, 190.0),
        (300.0, 455.0),
        20.0,
    )
    render(
        points,
        colors,
        args.output_dir / "02-front-deck-metric-top.png",
        "Current Lite3 Professional scan — front deck close-up",
        (80.0, 290.0),
        (-140.0, 140.0),
        (350.0, 435.0),
        10.0,
    )
    render(
        points,
        colors,
        args.output_dir / "03-front-deck-height-map.png",
        "Front deck maximum-height map — scan geometry, not texture",
        (80.0, 290.0),
        (-140.0, 140.0),
        (350.0, 435.0),
        10.0,
        height_mode=True,
    )
    render(
        points,
        colors,
        args.output_dir / "04-front-flat-deck-surface-band.png",
        "Front flat-deck surface band — texture; low holes remain blank",
        (100.0, 225.0),
        (-80.0, 80.0),
        (388.0, 408.0),
        5.0,
    )
    render(
        points,
        colors,
        args.output_dir / "05-front-flat-deck-height-band.png",
        "Front flat-deck surface band — 388 to 408 mm height",
        (100.0, 225.0),
        (-80.0, 80.0),
        (388.0, 408.0),
        5.0,
        height_mode=True,
    )


if __name__ == "__main__":
    main()
