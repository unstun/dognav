#!/usr/bin/env python3
"""Compose manual-versus-CAD review sheets for the V1.0.7 baseline."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
OUTPUT_ROOT = (
    TASK_ROOT / "evidence/official-lidar-v107-baseline-candidate"
)
MANUAL_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-design-drawings/derived"
)

FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/System/Library/Fonts/Helvetica.ttc"),
]


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def crop_white(
    image: Image.Image,
    margin: int = 24,
) -> Image.Image:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, "white")
    difference = ImageChops.difference(rgb, background).convert("L")
    mask = difference.point(lambda value: 255 if value > 8 else 0)
    box = mask.getbbox()
    if box is None:
        return rgb
    left = max(0, box[0] - margin)
    top = max(0, box[1] - margin)
    right = min(rgb.width, box[2] + margin)
    bottom = min(rgb.height, box[3] + margin)
    return rgb.crop((left, top, right, bottom))


def contain(
    image: Image.Image,
    size: tuple[int, int],
) -> Image.Image:
    fitted = ImageOps.contain(
        crop_white(image),
        size,
        method=Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", size, "white")
    x_value = (size[0] - fitted.width) // 2
    y_value = (size[1] - fitted.height) // 2
    canvas.paste(fitted, (x_value, y_value))
    return canvas


def pair_sheet(
    left_image: Image.Image,
    right_image: Image.Image,
    title: str,
    left_label: str,
    right_label: str,
    output_name: str,
) -> None:
    width = 2000
    height = 1120
    header = 92
    label_height = 58
    footer = 56
    panel_width = width // 2
    panel_height = height - header - label_height - footer
    canvas = Image.new("RGB", (width, height), (246, 247, 249))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (width // 2, 26),
        title,
        fill=(24, 28, 34),
        font=font(40),
        anchor="ma",
    )
    panels = [
        contain(left_image, (panel_width - 40, panel_height - 20)),
        contain(right_image, (panel_width - 40, panel_height - 20)),
    ]
    for index, panel in enumerate(panels):
        x_value = index * panel_width + 20
        y_value = header + label_height
        canvas.paste(panel, (x_value, y_value))
    draw.rectangle(
        (0, header, width, header + label_height),
        fill=(230, 233, 237),
    )
    draw.line(
        (panel_width, header, panel_width, height - footer),
        fill=(190, 194, 200),
        width=2,
    )
    draw.text(
        (panel_width // 2, header + label_height // 2),
        left_label,
        fill=(42, 46, 52),
        font=font(27),
        anchor="mm",
    )
    draw.text(
        (panel_width + panel_width // 2, header + label_height // 2),
        right_label,
        fill=(42, 46, 52),
        font=font(27),
        anchor="mm",
    )
    draw.rectangle(
        (0, height - footer, width, height),
        fill=(32, 36, 42),
    )
    draw.text(
        (width // 2, height - footer // 2),
        "Appearance baseline only - Interface and rigid registration are image estimates, not factory CAD",
        fill=(238, 240, 243),
        font=font(22),
        anchor="mm",
    )
    canvas.save(OUTPUT_ROOT / output_name)


def overview_sheet(
    official_front: Image.Image,
    candidate_front: Image.Image,
    official_side: Image.Image,
    candidate_side: Image.Image,
) -> None:
    width = 2000
    height = 1540
    header = 92
    footer = 64
    cell_width = width // 2
    cell_height = (height - header - footer) // 2
    canvas = Image.new("RGB", (width, height), (244, 246, 248))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (width // 2, 26),
        "Lite3 LiDAR V1.0.7 - Official Manual vs Current CAD Baseline",
        fill=(24, 28, 34),
        font=font(39),
        anchor="ma",
    )
    cells = [
        (official_front, "Official manual - front"),
        (candidate_front, "Current CAD - front"),
        (official_side, "Official manual - side"),
        (candidate_side, "Current CAD - side (mirrored to match)"),
    ]
    for index, (source, label) in enumerate(cells):
        column = index % 2
        row = index // 2
        x0 = column * cell_width
        y0 = header + row * cell_height
        draw.rectangle(
            (x0 + 10, y0 + 10, x0 + cell_width - 10, y0 + cell_height - 10),
            fill="white",
            outline=(194, 198, 204),
            width=2,
        )
        draw.text(
            (x0 + cell_width // 2, y0 + 33),
            label,
            fill=(42, 46, 52),
            font=font(25),
            anchor="mm",
        )
        panel = contain(
            source,
            (cell_width - 50, cell_height - 80),
        )
        canvas.paste(panel, (x0 + 25, y0 + 65))
    draw.rectangle(
        (0, height - footer, width, height),
        fill=(32, 36, 42),
    )
    draw.text(
        (width // 2, height - footer // 2),
        "Identity target: long Interface + forward/downward Mid-360 + front D435; BZ20/AGX/custom rails excluded",
        fill=(238, 240, 243),
        font=font(22),
        anchor="mm",
    )
    canvas.save(OUTPUT_ROOT / "official-v107-baseline-comparison.png")


def main() -> None:
    official_front = Image.open(
        MANUAL_ROOT / "lite3-lidar-v107-front-render-original.png"
    )
    official_side = Image.open(
        MANUAL_ROOT / "lite3-lidar-v107-side-render-original.png"
    )
    official_rear_line = Image.open(
        MANUAL_ROOT / "lite3-lidar-v107-rear-line-art-original.png"
    )
    candidate_front = Image.open(OUTPUT_ROOT / "full-standing-front.png")
    candidate_side_raw = Image.open(OUTPUT_ROOT / "full-standing-side.png")
    candidate_side = ImageOps.mirror(candidate_side_raw)
    candidate_iso = Image.open(OUTPUT_ROOT / "full-standing-isometric.png")

    pair_sheet(
        official_front,
        candidate_front,
        "Front silhouette and sensor-stack registration",
        "Official V1.0.7 manual",
        "Current source-backed CAD baseline",
        "official-vs-candidate-front.png",
    )
    pair_sheet(
        official_side,
        candidate_side,
        "Side silhouette, standing pose, and Interface placement",
        "Official V1.0.7 manual",
        "Current CAD (mirrored to same direction)",
        "official-vs-candidate-side.png",
    )
    pair_sheet(
        official_rear_line,
        candidate_iso,
        "Rear-isometric assembly identity",
        "Official V1.0.7 manual line art",
        "Current source-backed CAD baseline",
        "official-vs-candidate-isometric.png",
    )
    overview_sheet(
        official_front,
        candidate_front,
        official_side,
        candidate_side,
    )
    for name in (
        "official-vs-candidate-front.png",
        "official-vs-candidate-side.png",
        "official-vs-candidate-isometric.png",
        "official-v107-baseline-comparison.png",
    ):
        print(f"comparison={OUTPUT_ROOT / name}")


if __name__ == "__main__":
    main()
