#!/usr/bin/env python3
"""Create a source-versus-printable-model review sheet."""

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
OFFICIAL_MID360 = (
    REPO
    / "references/upstream/2026-07-24_livox-mid360-cad/source"
    / "official_images/mid360-product-detail.jpg"
)
MODEL_ISO = ROOT / "evidence/visual-reference-isometric.png"
MODEL_SIDE = ROOT / "evidence/visual-reference-mid360-side.png"
BUILD_REPORT = ROOT / "reports/build_report.json"
VALIDATION_REPORT = ROOT / "reports/validation_report.json"
SLICE_REPORT = ROOT / "reports/slice_report.json"
OUTPUT = ROOT / "evidence/lite3-lidar-printable-comparison.png"

CANVAS = (2600, 1940)
MARGIN = 75
GAP = 50
CARD_W = (CANVAS[0] - 2 * MARGIN - GAP) // 2
CARD_H = 670


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
    x: int,
    y: int,
    title: str,
    tag: str,
    tag_color: tuple[int, int, int],
) -> None:
    draw.rounded_rectangle(
        (x, y, x + CARD_W, y + CARD_H),
        radius=24,
        fill=(250, 251, 252),
        outline=(211, 216, 222),
        width=3,
    )
    fitted = contain(image, (CARD_W - 60, CARD_H - 125))
    canvas.paste(
        fitted,
        (
            x + (CARD_W - fitted.width) // 2,
            y + 86 + (CARD_H - 105 - fitted.height) // 2,
        ),
    )
    draw.text((x + 28, y + 23), title, font=font(36, True), fill=(24, 28, 33))
    tag_font = font(23, True)
    box = draw.textbbox((0, 0), tag, font=tag_font)
    width = box[2] - box[0] + 30
    tag_x = x + CARD_W - width - 28
    draw.rounded_rectangle(
        (tag_x, y + 21, tag_x + width, y + 62),
        radius=13,
        fill=tag_color,
    )
    draw.text((tag_x + 15, y + 27), tag, font=tag_font, fill="white")


def annotate_forward_down(image: Image.Image) -> Image.Image:
    source = image.convert("RGB")
    banner_height = 170
    annotated = Image.new(
        "RGB",
        (source.width, source.height + banner_height),
        "white",
    )
    annotated.paste(source, (0, banner_height))
    draw = ImageDraw.Draw(annotated)
    red = (198, 55, 48)
    start = (int(source.width * 0.34), 55)
    end = (int(source.width * 0.76), 125)
    draw.line((start, end), fill=red, width=13)
    draw.polygon(
        (
            end,
            (end[0] - 43, end[1] - 32),
            (end[0] - 52, end[1] + 24),
        ),
        fill=red,
    )
    draw.text(
        (48, 25),
        "机头 +X 在右侧",
        font=font(46, True),
        fill=(25, 30, 36),
    )
    draw.text(
        (48, 88),
        "安装平面向机头下降 15°",
        font=font(42, True),
        fill=red,
    )
    return annotated


def main() -> None:
    for path in (
        OFFICIAL_PRODUCT,
        OFFICIAL_MID360,
        MODEL_ISO,
        MODEL_SIDE,
        BUILD_REPORT,
        VALIDATION_REPORT,
        SLICE_REPORT,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    build = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION_REPORT.read_text(encoding="utf-8"))
    slicing = json.loads(SLICE_REPORT.read_text(encoding="utf-8"))
    if not validation["passed"] or not slicing["passed"]:
        raise ValueError("Comparison sheet requires passing validation and slicing")
    part_count = len(slicing["parts"])

    official = Image.open(OFFICIAL_PRODUCT)
    official_mid360 = Image.open(OFFICIAL_MID360)
    model_iso = Image.open(MODEL_ISO)
    model_side = annotate_forward_down(Image.open(MODEL_SIDE))

    canvas = Image.new("RGB", CANVAS, (237, 240, 244))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (MARGIN, 35),
        "Lite3 激光版：Mid-360 + D435i 可打印复刻",
        font=font(52, True),
        fill=(19, 24, 30),
    )
    draw.text(
        (MARGIN, 96),
        "官方高精外观参考 + 独立水密打印轨 + 真实 D435i、两件式支架与实体承接耳",
        font=font(28),
        fill=(77, 85, 95),
    )

    draw_card(
        canvas,
        draw,
        official,
        MARGIN,
        150,
        "官方 Lite3 LiDAR 产品图",
        "官方证据",
        (42, 94, 170),
    )
    draw_card(
        canvas,
        draw,
        model_iso,
        MARGIN + CARD_W + GAP,
        150,
        "1:1 官方机身装配视觉参考",
        "视觉参考",
        (151, 96, 32),
    )
    draw_card(
        canvas,
        draw,
        official_mid360,
        MARGIN,
        860,
        "Livox Mid-360 官方产品图",
        "官方证据",
        (42, 94, 170),
    )
    draw_card(
        canvas,
        draw,
        model_side,
        MARGIN + CARD_W + GAP,
        860,
        "侧视：真实 Mid-360 向机头下降 15°",
        "视觉参考",
        (151, 96, 32),
    )

    box_y = 1570
    draw.rounded_rectangle(
        (MARGIN, box_y, CANVAS[0] - MARGIN, 1875),
        radius=24,
        fill="white",
        outline=(211, 216, 222),
        width=3,
    )
    envelope = build["standing_reference_1_1"]["bbox_size_mm"]
    envelope_text = " × ".join(f"{value:.2f}" for value in envelope)
    draw.text(
        (MARGIN + 32, box_y + 28),
        f"官方包络 610 × 370 × 496 mm；复刻包络 {envelope_text} mm",
        font=font(32, True),
        fill=(24, 29, 35),
    )
    draw.text(
        (MARGIN + 32, box_y + 82),
        f"无跨接底板：Interface 局部脚座与雷达局部安装点独立；{part_count} 个 1:4 STL 全部水密流形。",
        font=font(28),
        fill=(45, 53, 62),
    )
    fallback_count = sum(
        len(part["nonblocking_slicer_fallback_lines"])
        for part in slicing["parts"].values()
    )
    draw.text(
        (MARGIN + 32, box_y + 132),
        f"切片：PrusaSlicer 2.9.6，{part_count}/{part_count} 非空 G-code，0 个阻断诊断；记录 {fallback_count} 条非阻断 Voronoi 数值回退。",
        font=font(28),
        fill=(45, 53, 62),
    )
    draw.text(
        (MARGIN + 32, box_y + 188),
        "真实边界：Mid-360/J20A/S410 是官方源几何，D435i 使用官方 ROS 网格；完整支架不是厂家生产 CAD 或实物适配验证。",
        font=font(28, True),
        fill=(151, 62, 43),
    )
    draw.text(
        (MARGIN + 32, box_y + 238),
        "雷达前下倾 15°，D435i 下倾 20°；8 颗支架螺钉中，载体侧 2 颗进入 S410 集成盲孔承接耳，不再悬空。",
        font=font(25),
        fill=(101, 69, 45),
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, optimize=True)
    print(f"comparison={OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
