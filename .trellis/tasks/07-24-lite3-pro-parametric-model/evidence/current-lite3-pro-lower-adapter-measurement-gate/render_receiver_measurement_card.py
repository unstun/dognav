"""Render a Chinese physical-measurement card for the current Lite3 Pro deck."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


GATE_DIR = Path(__file__).resolve().parent
PARAMETERS_PATH = GATE_DIR / "parameters.json"
REQUEST_PATH = GATE_DIR / "receiver_measurement_request.json"
OUTPUT_DIR = GATE_DIR / "renders"
OUTPUT_PATH = OUTPUT_DIR / "current-lite3-pro-receiver-measurement-card-rev-b.png"

WIDTH = 1800
HEIGHT = 1200
BACKGROUND = "#F3F5F7"
INK = "#17212B"
MUTED = "#52606D"
DECK = "#E9EDF1"
DECK_EDGE = "#8A99A8"
ENCLOSURE = "#556270"
ENCLOSURE_EDGE = "#202B35"
KEEPOUT = "#C23B53"
BLUE = "#1677FF"
YELLOW = "#F5B700"
GREEN = "#00A878"
WHITE = "#FFFFFF"
RED = "#D62828"

FONT_PATHS = [
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
]


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def rounded_label(
    draw: ImageDraw.ImageDraw,
    centre: tuple[float, float],
    text: str,
    fill: str,
    radius: int = 24,
) -> None:
    x, y = centre
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline=WHITE, width=4)
    bbox = draw.textbbox((0, 0), text, font=font(28))
    draw.text(
        (x - (bbox[2] - bbox[0]) / 2, y - (bbox[3] - bbox[1]) / 2 - 2),
        text,
        fill=WHITE if fill != YELLOW else INK,
        font=font(28),
    )


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    colour: str,
    width: int = 5,
) -> None:
    draw.line((start, end), fill=colour, width=width)
    x0, y0 = start
    x1, y1 = end
    dx, dy = x1 - x0, y1 - y0
    length = max((dx * dx + dy * dy) ** 0.5, 1.0)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    head = 15
    wing = 8
    draw.polygon(
        [
            (x1, y1),
            (x1 - ux * head + px * wing, y1 - uy * head + py * wing),
            (x1 - ux * head - px * wing, y1 - uy * head - py * wing),
        ],
        fill=colour,
    )


def main() -> None:
    parameters = json.loads(PARAMETERS_PATH.read_text(encoding="utf-8"))
    request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    keepout = parameters["compute_enclosure_keepout"]
    polygon = keepout["nominal_footprint_polygon_mm"]

    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.text((70, 50), "Lite3 专业版｜底座孔位与工控机凹口实测卡", fill=INK, font=font(46))
    draw.text(
        (72, 112),
        "蓝色 A/B：前面两个小孔　黄色 C：中间候选孔　灰色：扫描得到的双凹口工控机外形",
        fill=MUTED,
        font=font(25),
    )

    panel = (55, 175, 1015, 975)
    draw.rounded_rectangle(panel, radius=28, fill=WHITE, outline="#D5DCE3", width=3)
    draw.text((85, 198), "俯视示意（+X 朝机器狗头部）", fill=INK, font=font(30))

    plot_left, plot_top, plot_right, plot_bottom = 110, 270, 960, 920
    x_min, x_max = -315.0, 25.0
    y_min, y_max = -80.0, 80.0
    scale = min((plot_right - plot_left) / (y_max - y_min), (plot_bottom - plot_top) / (x_max - x_min))
    centre_screen_x = (plot_left + plot_right) / 2

    def to_screen(point: tuple[float, float] | list[float]) -> tuple[float, float]:
        x_mm, y_mm = point
        sx = centre_screen_x - y_mm * scale
        sy = plot_top + (x_max - x_mm) * scale
        return sx, sy

    deck_points = [to_screen((x, y)) for x, y in [(-310, -67), (20, -67), (20, 67), (-310, 67)]]
    deck_bounds = (
        min(p[0] for p in deck_points),
        min(p[1] for p in deck_points),
        max(p[0] for p in deck_points),
        max(p[1] for p in deck_points),
    )
    draw.rounded_rectangle(deck_bounds, radius=45, fill=DECK, outline=DECK_EDGE, width=4)

    keep = keepout["expanded_proxy_bounds_mm"]
    keep_a = to_screen((keep["x"][1], keep["y"][1]))
    keep_b = to_screen((keep["x"][0], keep["y"][0]))
    keep_rect = (
        min(keep_a[0], keep_b[0]),
        min(keep_a[1], keep_b[1]),
        max(keep_a[0], keep_b[0]),
        max(keep_a[1], keep_b[1]),
    )
    draw.rounded_rectangle(keep_rect, radius=18, outline=KEEPOUT, width=4)

    enclosure_points = [to_screen((point[0], point[1])) for point in polygon]
    draw.polygon(enclosure_points, fill=ENCLOSURE, outline=ENCLOSURE_EDGE)
    draw.line(enclosure_points + [enclosure_points[0]], fill=ENCLOSURE_EDGE, width=5, joint="curve")

    recess = keepout["front_side_recesses"]
    recess_boxes = [
        [
            (recess["front_x_mm"], recess["left_inner_y_mm"]),
            (recess["shoulder_x_mm"], keepout["left_edge_y_mm"]),
        ],
        [
            (recess["front_x_mm"], keepout["right_edge_y_mm"]),
            (recess["shoulder_x_mm"], recess["right_inner_y_mm"]),
        ],
    ]
    for first, second in recess_boxes:
        p0, p1 = to_screen(first), to_screen(second)
        rect = (min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1]))
        draw.rounded_rectangle(rect, radius=6, fill="#FFD6DE", outline=KEEPOUT, width=3)
        for offset in range(-30, 70, 12):
            draw.line((rect[0] + offset, rect[3], rect[0] + offset + 30, rect[1]), fill="#E88999", width=2)

    receiver_colours = {"A": BLUE, "B": BLUE, "C": YELLOW}
    receiver_positions: dict[str, tuple[float, float]] = {}
    for point in request["receiver_points"]:
        x_mm, y_mm, _ = point["axis_mm"]
        position = to_screen((x_mm, y_mm))
        receiver_positions[point["callout"]] = position
        draw.ellipse((position[0] - 16, position[1] - 16, position[0] + 16, position[1] + 16), fill=WHITE, outline=receiver_colours[point["callout"]], width=7)
        rounded_label(draw, (position[0] + 34, position[1] + 38), point["callout"], receiver_colours[point["callout"]])

    a = receiver_positions["A"]
    b = receiver_positions["B"]
    dim_y = min(a[1], b[1]) - 55
    draw.line((a[0], a[1] - 20, a[0], dim_y), fill=BLUE, width=3)
    draw.line((b[0], b[1] - 20, b[0], dim_y), fill=BLUE, width=3)
    arrow(draw, (a[0], dim_y), (b[0], dim_y), BLUE, 3)
    arrow(draw, (b[0], dim_y + 1), (a[0], dim_y + 1), BLUE, 3)
    pitch_text = "轴距 65.0 ± 1.0 mm"
    pitch_box = draw.textbbox((0, 0), pitch_text, font=font(23))
    draw.rounded_rectangle(
        (
            (a[0] + b[0]) / 2 - (pitch_box[2] - pitch_box[0]) / 2 - 10,
            dim_y - 36,
            (a[0] + b[0]) / 2 + (pitch_box[2] - pitch_box[0]) / 2 + 10,
            dim_y - 2,
        ),
        radius=8,
        fill=WHITE,
    )
    draw.text(((a[0] + b[0]) / 2 - (pitch_box[2] - pitch_box[0]) / 2, dim_y - 34), pitch_text, fill=BLUE, font=font(23))

    arrow(draw, (900, 390), (730, 460), KEEPOUT, 5)
    draw.text((700, 340), "两处小凹口\n已进入真实外轮廓", fill=KEEPOUT, font=font(27), spacing=8)
    draw.text((320, 750), "工控机（扫描轮廓）", fill=WHITE, font=font(28))
    draw.text((260, 800), "红色虚线范围仍按保守碰撞禁入区处理", fill="#FFE1E6", font=font(20))

    origin = (205, 900)
    arrow(draw, origin, (origin[0], origin[1] - 75), GREEN, 6)
    arrow(draw, origin, (origin[0] - 75, origin[1]), GREEN, 6)
    draw.text((origin[0] + 10, origin[1] - 85), "+X 前", fill=GREEN, font=font(22))
    draw.text((origin[0] - 135, origin[1] + 10), "+Y 左", fill=GREEN, font=font(22))

    right_x = 1050
    draw.rounded_rectangle((1035, 175, 1745, 975), radius=28, fill=WHITE, outline="#D5DCE3", width=3)
    draw.text((right_x + 25, 205), "需要补齐的实物证据", fill=INK, font=font(34))

    sections = [
        ("A / B", BLUE, "两个前孔分别确认（不要只量一个）", ["螺纹规格", "有效螺纹深度", "沉孔直径 / 深度", "金属嵌件与下方承力路径"]),
        ("C", YELLOW, "先判断它到底是什么", ["承力螺纹孔？", "只是盖板螺丝？", "若可承力，再量螺纹和有效深度"]),
        ("D", GREEN, "工控机周围不可占用区域", ["脚垫 / 通风口", "插头和线缆弯曲空间", "盖板拆装方向", "六角扳手操作空间"]),
    ]
    y = 270
    for label, colour, subtitle, bullets in sections:
        rounded_label(draw, (right_x + 55, y + 20), label, colour, radius=27)
        draw.text((right_x + 100, y), subtitle, fill=INK, font=font(26))
        y += 58
        for bullet in bullets:
            draw.ellipse((right_x + 102, y + 9, right_x + 112, y + 19), fill=colour)
            draw.text((right_x + 128, y), bullet, fill=MUTED, font=font(23))
            y += 40
        y += 24

    draw.rounded_rectangle((55, 1005, 1745, 1150), radius=26, fill="#FFF3CD", outline="#E0A800", width=3)
    draw.text((88, 1025), "测量安全边界", fill=RED, font=font(30))
    draw.text(
        (88, 1070),
        "断电操作；只可用螺纹规或已知松螺丝手拧试配；禁止电动工具、禁止硬拧，禁止为了识别规格拆卸承力或密封螺丝。",
        fill=INK,
        font=font(24),
    )
    draw.text((1210, 1120), "未完成 A/B/C/D → 不生成打印底座", fill=RED, font=font(22))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_PATH, optimize=True)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
