#!/usr/bin/env python3
"""Build a visual evidence sheet for the corrected FAST-LIVO2 layout."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
OUTPUT_ROOT = TASK_ROOT / "evidence/official-bz20-layout-candidate"
VIDEO_ROOT = (
    REPO_ROOT
    / "references/upstream"
    / "2026-07-26_lite3-official-fast-livo2-install-video"
    / "derived/sensor-install"
)

CANVAS_SIZE = (2400, 1800)
PANEL_SIZE = (1120, 690)
PANEL_POSITIONS = [
    (60, 170),
    (1220, 170),
    (60, 980),
    (1220, 980),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path(
            "/System/Library/Fonts/PingFang.ttc"
        ),
        Path(
            "/System/Library/Fonts/STHeiti Medium.ttc"
            if bold
            else "/System/Library/Fonts/STHeiti Light.ttc"
        ),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(
                str(candidate),
                size=size,
                index=1 if bold and candidate.suffix == ".ttc" else 0,
            )
    return ImageFont.load_default()


def fitted_panel(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    return ImageOps.contain(
        image,
        PANEL_SIZE,
        method=Image.Resampling.LANCZOS,
    )


def paste_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    path: Path,
    position: tuple[int, int],
    label: str,
    label_color: tuple[int, int, int],
) -> None:
    x, y = position
    draw.rounded_rectangle(
        [x, y, x + PANEL_SIZE[0], y + PANEL_SIZE[1]],
        radius=24,
        fill=(247, 248, 250),
        outline=(205, 210, 218),
        width=3,
    )
    image = fitted_panel(path)
    paste_x = x + (PANEL_SIZE[0] - image.width) // 2
    paste_y = y + (PANEL_SIZE[1] - image.height) // 2
    canvas.paste(image, (paste_x, paste_y))
    badge_font = font(33, bold=True)
    bbox = draw.textbbox((0, 0), label, font=badge_font)
    badge_width = bbox[2] - bbox[0] + 40
    draw.rounded_rectangle(
        [x + 18, y + 18, x + 18 + badge_width, y + 70],
        radius=14,
        fill=label_color,
    )
    draw.text(
        (x + 38, y + 26),
        label,
        font=badge_font,
        fill=(255, 255, 255),
    )


def main() -> None:
    canvas = Image.new("RGB", CANVAS_SIZE, (235, 238, 243))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (60, 42),
        "Lite3 官方 FAST-LIVO2 传感器总成：来源对照",
        font=font(54, bold=True),
        fill=(30, 36, 46),
    )
    draw.text(
        (60, 108),
        "保留 J17A / J20A / S410 / Mid-360 / D435 / BZ20；删除导轨、托板和假 Jetson",
        font=font(31),
        fill=(75, 84, 98),
    )

    panels = [
        (
            VIDEO_ROOT / "frame-296s.jpg",
            "官方视频 296 s",
            (32, 102, 174),
        ),
        (
            OUTPUT_ROOT / "full-standing-isometric.png",
            "CAD 官方源几何",
            (24, 132, 92),
        ),
        (
            VIDEO_ROOT / "frame-284s.jpg",
            "官方底面 284 s",
            (32, 102, 174),
        ),
        (
            OUTPUT_ROOT / "mounting-relationships-bottom.png",
            "CAD 孔轴关系（非定长螺丝）",
            (24, 132, 92),
        ),
    ]
    for panel, position in zip(panels, PANEL_POSITIONS):
        path, label, color = panel
        paste_panel(canvas, draw, path, position, label, color)

    draw.rounded_rectangle(
        [60, 1700, 2340, 1760],
        radius=18,
        fill=(255, 244, 220),
        outline=(225, 177, 75),
        width=2,
    )
    draw.text(
        (86, 1712),
        "边界：后部工控机与 Lite3 Pro 定制底座尚未建模；需要实际工控机尺寸/孔位后才能定稿。",
        font=font(29, bold=True),
        fill=(122, 76, 13),
    )

    output_path = OUTPUT_ROOT / "official-video-vs-source-cad.png"
    canvas.save(output_path, quality=95)
    print(output_path)


if __name__ == "__main__":
    main()
