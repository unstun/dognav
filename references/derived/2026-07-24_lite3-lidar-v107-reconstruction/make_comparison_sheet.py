#!/usr/bin/env python3
"""Create a durable official-source versus reconstruction comparison sheet."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OFFICIAL_PRODUCT = (
    REPO
    / ".trellis/tasks/07-24-lite3-pro-parametric-model/evidence"
    / "lite3-official-lidar-product.png"
)
OFFICIAL_MANUAL = (
    REPO
    / "references/upstream/2026-07-24_lite3-design-drawings/derived"
    / "lite3-lidar-manual-07.png"
)
RENDER = ROOT / "evidence/freecad-isometric.png"
UPPER_TOP = ROOT / "evidence/upper-module-top.png"
VALIDATION = ROOT / "reports/validation.json"
OUTPUT = ROOT / "evidence/lite3-lidar-v107-comparison.png"

CANVAS_SIZE = (2600, 1800)
MARGIN = 80
GAP = 55
CARD_W = (CANVAS_SIZE[0] - 2 * MARGIN - GAP) // 2
CARD_H = 650


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = (
        "/System/Library/Fonts/STHeiti Medium.ttc"
        if bold
        else "/System/Library/Fonts/STHeiti Light.ttc"
    )
    return ImageFont.truetype(path, size=size)


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.contain(image.convert("RGB"), size, Image.Resampling.LANCZOS)


def draw_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
    xy: tuple[int, int],
    title: str,
    tag: str,
    tag_color: tuple[int, int, int],
) -> None:
    x, y = xy
    draw.rounded_rectangle(
        (x, y, x + CARD_W, y + CARD_H),
        radius=22,
        fill=(248, 249, 250),
        outline=(215, 219, 224),
        width=3,
    )
    fitted = contain(image, (CARD_W - 70, CARD_H - 130))
    image_x = x + (CARD_W - fitted.width) // 2
    image_y = y + 88 + (CARD_H - 115 - fitted.height) // 2
    canvas.paste(fitted, (image_x, image_y))
    draw.text((x + 28, y + 23), title, fill=(26, 30, 34), font=font(36, True))
    tag_font = font(24, True)
    tag_box = draw.textbbox((0, 0), tag, font=tag_font)
    tag_w = tag_box[2] - tag_box[0] + 28
    tag_x = x + CARD_W - tag_w - 28
    draw.rounded_rectangle(
        (tag_x, y + 22, tag_x + tag_w, y + 61),
        radius=12,
        fill=tag_color,
    )
    draw.text((tag_x + 14, y + 26), tag, fill="white", font=tag_font)


def main() -> None:
    required = (
        OFFICIAL_PRODUCT,
        OFFICIAL_MANUAL,
        RENDER,
        UPPER_TOP,
        VALIDATION,
    )
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)

    with VALIDATION.open("r", encoding="utf-8") as handle:
        validation = json.load(handle)
    assembly_size = validation["assembly_bbox"]["size_mm"]

    official_product = Image.open(OFFICIAL_PRODUCT)
    manual = Image.open(OFFICIAL_MANUAL)
    official_manual_crop = manual.crop((100, 180, 1140, 745))
    render = Image.open(RENDER)
    upper_top = Image.open(UPPER_TOP)

    canvas = Image.new("RGB", CANVAS_SIZE, (238, 241, 244))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (MARGIN, 42),
        "Lite3 LiDAR V1.0.7：官方证据与三维复现",
        fill=(20, 24, 29),
        font=font(54, True),
    )

    draw_card(
        canvas,
        draw,
        official_product,
        (MARGIN, 130),
        "官方产品图",
        "官方证据",
        (45, 100, 180),
    )
    draw_card(
        canvas,
        draw,
        render,
        (MARGIN + CARD_W + GAP, 130),
        "FreeCAD 整机站立复现",
        "本次建模",
        (25, 133, 86),
    )
    draw_card(
        canvas,
        draw,
        official_manual_crop,
        (MARGIN, 825),
        "官方手册 V1.0.7 部件布局",
        "官方证据",
        (45, 100, 180),
    )
    draw_card(
        canvas,
        draw,
        upper_top,
        (MARGIN + CARD_W + GAP, 825),
        "上装俯视与四孔安装参考",
        "本次建模",
        (25, 133, 86),
    )

    measured = " × ".join(f"{value:.2f}" for value in assembly_size)
    draw.rounded_rectangle(
        (MARGIN, 1525, CANVAS_SIZE[0] - MARGIN, 1740),
        radius=22,
        fill=(255, 255, 255),
        outline=(215, 219, 224),
        width=3,
    )
    draw.text(
        (MARGIN + 30, 1555),
        f"官方站立外形：610 × 370 × 496 mm    复现包络：{measured} mm",
        fill=(20, 24, 29),
        font=font(34, True),
    )
    draw.text(
        (MARGIN + 30, 1612),
        "激光雷达、散热片、保护环、接口盒、前置传感器条均为可单独编辑实体；四孔采用官方 74 × 94 mm、4×M3 名义参考。",
        fill=(52, 58, 64),
        font=font(29),
    )
    draw.text(
        (MARGIN + 30, 1662),
        "边界：当前是外观复现和视觉装配，不是厂家生产 CAD；未公开的壳体尺寸与细节均标注为图像估算。",
        fill=(152, 65, 45),
        font=font(27, True),
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, optimize=True)
    print(f"comparison={OUTPUT}")


if __name__ == "__main__":
    main()

