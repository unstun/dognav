#!/usr/bin/env python3
"""Create a reviewer-facing official-video versus CAD comparison sheet."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
EVIDENCE_ROOT = TASK_ROOT / "evidence/j17a-direct-camera-candidate"
VIDEO_ROOT = (
    REPO_ROOT
    / "references/upstream/"
    "2026-07-26_lite3-official-fast-livo2-install-video/"
    "derived/sensor-install"
)
OUTPUT = EVIDENCE_ROOT / "official-vs-cad-direct-mount-comparison.png"

FONT_CANDIDATES = [
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
]


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = image.convert("RGB")
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    x = (size[0] - copy.width) // 2
    y = (size[1] - copy.height) // 2
    canvas.paste(copy, (x, y))
    return canvas


def panel(
    source: Path,
    title: str,
    subtitle: str,
    size: tuple[int, int],
) -> Image.Image:
    title_height = 98
    image_area = (size[0], size[1] - title_height)
    result = Image.new("RGB", size, "#f6f7f8")
    draw = ImageDraw.Draw(result)
    draw.text((22, 13), title, fill="#111820", font=font(34))
    draw.text((22, 55), subtitle, fill="#5b6570", font=font(23))
    source_image = contain(Image.open(source), image_area)
    result.paste(source_image, (0, title_height))
    draw.rectangle(
        [(0, 0), (size[0] - 1, size[1] - 1)],
        outline="#c6ccd2",
        width=3,
    )
    return result


def main() -> None:
    canvas_width = 2480
    canvas_height = 1780
    margin = 54
    gap = 34
    heading_height = 150
    panel_width = (canvas_width - 2 * margin - gap) // 2
    panel_height = (canvas_height - heading_height - margin - gap) // 2

    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 28),
        "Lite3 官方 MID360 扩展：原始安装证据与 CAD 直接安装候选",
        fill="#111820",
        font=font(48),
    )
    draw.text(
        (margin, 90),
        "灰色 J17A、真实 MID360 / S410 / J20A、真实 D435；无导轨、无托板、无后置叉架",
        fill="#4b5560",
        font=font(28),
    )

    panels = [
        panel(
            VIDEO_ROOT / "frame-284s.jpg",
            "官方视频 284 s：组件底面",
            "D435 直接贴合 J17A 前端两块斜面",
            (panel_width, panel_height),
        ),
        panel(
            EVIDENCE_ROOT / "sensor-direct-bottom.png",
            "CAD 候选：同一底面关系",
            "45 mm 两孔；仅两颗 M3 轴线，17 mm 假间隙已删除",
            (panel_width, panel_height),
        ),
        panel(
            VIDEO_ROOT / "frame-292s.jpg",
            "官方视频 292 s：装到 Lite3 Venture",
            "雷达组件在前，Interface 紧邻其后",
            (panel_width, panel_height),
        ),
        panel(
            EVIDENCE_ROOT / "body-context-collision-isometric.png",
            "CAD 诊断：当前工控机占位体冲突",
            "红色为 3105 mm³ 穿模区；只应改隐藏底座后端",
            (panel_width, panel_height),
        ),
    ]

    positions = [
        (margin, heading_height),
        (margin + panel_width + gap, heading_height),
        (margin, heading_height + panel_height + gap),
        (
            margin + panel_width + gap,
            heading_height + panel_height + gap,
        ),
    ]
    for item, position in zip(panels, positions, strict=True):
        canvas.paste(item, position)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, quality=95)
    print(f"comparison={OUTPUT}")


if __name__ == "__main__":
    main()
