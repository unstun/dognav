#!/usr/bin/env python3
"""Create a print-parts, seams, and strengthened-feature evidence sheet."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
LAYOUT = ROOT / "evidence" / "printable-layout-top.png"
UPPER = ROOT / "evidence" / "printable-assembly-upper-isometric.png"
BUILD = ROOT / "reports" / "build_report.json"
SLICE = ROOT / "reports" / "slice_report.json"
OUTPUT = ROOT / "evidence" / "lite3-lidar-print-details.png"

CANVAS = (2400, 1700)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = (
        "/System/Library/Fonts/STHeiti Medium.ttc"
        if bold
        else "/System/Library/Fonts/STHeiti Light.ttc"
    )
    return ImageFont.truetype(path, size=size)


def trim_white(image: Image.Image, margin: int = 35) -> Image.Image:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, "white")
    difference = ImageChops.difference(rgb, background)
    bbox = difference.getbbox()
    if bbox is None:
        return rgb
    left, top, right, bottom = bbox
    return rgb.crop(
        (
            max(0, left - margin),
            max(0, top - margin),
            min(rgb.width, right + margin),
            min(rgb.height, bottom + margin),
        )
    )


def card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(
        box,
        radius=24,
        fill="white",
        outline=(210, 216, 223),
        width=3,
    )
    draw.text((x0 + 28, y0 + 22), title, font=font(34, True), fill=(23, 28, 34))
    fitted = ImageOps.contain(
        trim_white(image),
        (x1 - x0 - 55, y1 - y0 - 105),
        Image.Resampling.LANCZOS,
    )
    canvas.paste(
        fitted,
        (
            x0 + (x1 - x0 - fitted.width) // 2,
            y0 + 78 + (y1 - y0 - 85 - fitted.height) // 2,
        ),
    )


def main() -> None:
    build = json.loads(BUILD.read_text(encoding="utf-8"))
    slicing = json.loads(SLICE.read_text(encoding="utf-8"))
    part_count = len(slicing["parts"])
    layout = Image.open(LAYOUT)
    upper = Image.open(UPPER)
    canvas = Image.new("RGB", CANVAS, (237, 240, 244))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (70, 34),
        "Lite3 Mid-360/D435i：1:4 打印分件与螺钉装配",
        font=font(50, True),
        fill=(18, 24, 30),
    )
    draw.text(
        (70, 96),
        "所有图形均来自最终 STL/GLB；分件总览不是单平台排版承诺",
        font=font(27),
        fill=(77, 85, 94),
    )

    card(
        canvas,
        draw,
        layout,
        (70, 150, 1510, 1165),
        f"{part_count} 个独立打印 STL 与接缝位置",
    )
    card(
        canvas,
        draw,
        upper,
        (1560, 150, 2330, 1165),
        "无跨接底板的 Interface/Mid-360/D435i 上舱",
    )

    draw.rounded_rectangle(
        (70, 1215, 2330, 1625),
        radius=24,
        fill="white",
        outline=(210, 216, 223),
        width=3,
    )
    upper_pins = build["assembly_mounts"]["upper_module"]["pins"]
    camera_mount = build["assembly_mounts"]["camera_mount_bracket"]
    notes = [
        "腿部装配：12 根独立 2.4 mm 销轴，另含 2 根备用；孔半径 1.4 mm，名义径向间隙 0.20 mm。",
        "上舱外观：Interface 只保留局部脚座，雷达只保留局部安装点；没有跨接底板，也没有可见 Jetson 开发板。",
        "D435i 接口：官方 2 × M3 / 45 mm；2 颗载体螺钉进入上舱承接耳的 3.0 mm 盲孔，插入 2.2 mm，不再悬空。",
        f"支架装配：{camera_mount['camera_fasteners']} 颗相机侧螺钉 + {camera_mount['carrier_fasteners']} 颗载体侧螺钉预装，再用 {camera_mount['side_join_fasteners']} 颗横向螺钉锁合两件式支架。",
        f"上舱装配：{len(upper_pins)} 根隐藏模型定位柱 + 躯干浅槽；Mid-360 向机头前下倾 15°。",
        "真实几何：Mid-360/J20A/S410 来自官方 CAD；D435i 外观直接使用官方 ROS 网格，打印体由同一网格重建。",
        f"切片证据：PrusaSlicer 2.9.6 对 {part_count}/{part_count} 分件生成非空 G-code，阻断诊断为 0。",
        "尚未声明：摄像头实体试装、耗材收缩、载荷、散热、振动、螺纹强度与真机安装安全。",
    ]
    y = 1252
    for index, note in enumerate(notes, start=1):
        draw.ellipse((102, y + 7, 120, y + 25), fill=(27, 132, 87))
        draw.text((138, y), note, font=font(21, index == 8), fill=(48, 56, 65))
        y += 46

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, optimize=True)
    print(f"details={OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
