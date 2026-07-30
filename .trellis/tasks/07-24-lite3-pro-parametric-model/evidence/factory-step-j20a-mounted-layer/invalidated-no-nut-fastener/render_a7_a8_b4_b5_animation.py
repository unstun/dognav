from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "a7-a8-b4-b5-clean-animation-frames"
OUT = ROOT / "a7-a8-b4-b5-clean-annotated-frames"
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
OUT.mkdir(parents=True, exist_ok=True)

TITLE = ImageFont.truetype(FONT_PATH, 32)
LABEL = ImageFont.truetype(FONT_PATH, 25)
SMALL = ImageFont.truetype(FONT_PATH, 19)
TINY = ImageFont.truetype(FONT_PATH, 16)


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def arrow(draw: ImageDraw.ImageDraw, start, end, color, width=5):
    draw.line([start, end], fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 13
    p1 = (
        end[0] - size * math.cos(angle - math.pi / 6),
        end[1] - size * math.sin(angle - math.pi / 6),
    )
    p2 = (
        end[0] - size * math.cos(angle + math.pi / 6),
        end[1] - size * math.sin(angle + math.pi / 6),
    )
    draw.polygon([end, p1, p2], fill=color)


def panel(image, xy, fill, outline=None, radius=14, width=2):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    image.alpha_composite(overlay)


def annotate(path: Path) -> Path:
    index = int(path.stem.split("_")[-1])
    image = Image.open(path).convert("RGBA")

    panel(image, (18, 14, 1120, 64), (14, 34, 58, 224), (65, 181, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text(
        (36, 20),
        "A7/A8 ↔ B4/B5：支架一与支架二孔位对接动画",
        font=TITLE,
        fill="white",
    )

    if index < 15:
        stage = "1  黄色 A7/A8 固定；蓝色 B4/B5 随支架二保持分离"
        bracket_progress = 0.0
    elif index <= 59:
        stage = "2  支架二沿装配方向靠近：B4 → A7，B5 → A8"
        bracket_progress = ease((index - 15) / 44.0)
    elif index < 79:
        stage = "3  蓝环套入黄环：A7/B4 与 A8/B5 的孔中心重合"
        bracket_progress = 1.0
    elif index <= 119:
        stage = "4  只出现两颗红色演示螺钉，并沿两条确认轴线旋入"
        bracket_progress = 1.0
    else:
        stage = "5  终态：A7 ↔ B4、A8 ↔ B5；没有残留 M3×8 螺钉"
        bracket_progress = 1.0

    panel(image, (18, 560, 1125, 706), (250, 251, 252, 229), (25, 63, 92, 235))
    draw = ImageDraw.Draw(image)
    draw.text((38, 572), stage, font=LABEL, fill=(12, 48, 77, 255))
    draw.rounded_rectangle((40, 615, 64, 639), radius=5, fill=(255, 205, 0, 255))
    draw.text((76, 610), "黄色：支架一 A7/A8", font=SMALL, fill=(25, 25, 25, 255))
    draw.rounded_rectangle((315, 615, 339, 639), radius=5, fill=(0, 140, 255, 255))
    draw.text((351, 610), "蓝色：支架二 B4/B5", font=SMALL, fill=(25, 25, 25, 255))
    draw.rounded_rectangle((618, 615, 642, 639), radius=5, fill=(245, 50, 25, 255))
    draw.text((654, 610), "红色：两颗前端演示螺钉", font=SMALL, fill=(25, 25, 25, 255))
    draw.text(
        (40, 652),
        "这版只验证你确认的孔位映射与装配路径；螺纹、最终长度、扭矩和承载仍不是实物定案。",
        font=SMALL,
        fill=(92, 48, 25, 255),
    )
    draw.text(
        (40, 680),
        "组件计数：黄色环 2、蓝色环 2、红色螺钉 2；旧 FRONT_M3x8 组件为 0。",
        font=TINY,
        fill=(40, 75, 96, 255),
    )

    yellow_positions = [(565, 159), (684, 192)]
    blue_starts = [(628, 115), (747, 147)]
    blue_positions = []
    for start, end in zip(blue_starts, yellow_positions):
        blue_positions.append(
            (
                round(start[0] + (end[0] - start[0]) * bracket_progress),
                round(start[1] + (end[1] - start[1]) * bracket_progress),
            )
        )

    if index <= 59:
        for blue, yellow in zip(blue_positions, yellow_positions):
            draw.ellipse(
                (blue[0] - 20, blue[1] - 20, blue[0] + 20, blue[1] + 20),
                outline=(0, 140, 255, 255),
                width=4,
            )
            arrow(draw, blue, yellow, (0, 140, 255, 255), 4)
        draw.text((840, 110), "蓝环向黄环靠近", font=LABEL, fill=(0, 92, 175, 255))
    elif index < 79:
        for point in yellow_positions:
            draw.ellipse(
                (point[0] - 25, point[1] - 25, point[0] + 25, point[1] + 25),
                outline=(28, 175, 83, 255),
                width=6,
            )
        draw.text((825, 110), "两组孔已重合", font=LABEL, fill=(10, 120, 58, 255))
    elif index >= 120:
        draw.rounded_rectangle(
            (822, 102, 1220, 148),
            radius=10,
            fill=(225, 249, 233, 238),
            outline=(22, 148, 73, 255),
            width=3,
        )
        draw.text((842, 110), "两颗螺钉已到终点", font=LABEL, fill=(12, 105, 52, 255))

    destination = OUT / path.name
    image.convert("RGB").save(destination, quality=95)
    return destination


raw_frames = sorted(RAW.glob("frame_*.png"))
if len(raw_frames) != 135:
    raise RuntimeError(f"Expected 135 raw frames, found {len(raw_frames)}")

annotated = [annotate(path) for path in raw_frames]

selected = [
    (0, "分离"),
    (38, "支架二靠近"),
    (70, "孔位重合"),
    (100, "两颗螺钉旋入"),
    (134, "终态"),
]
sheet = Image.new("RGB", (1920, 820), "white")
positions = [(0, 0), (640, 0), (1280, 0), (320, 410), (960, 410)]
for (frame_index, caption), position in zip(selected, positions):
    frame = Image.open(annotated[frame_index]).convert("RGB").resize(
        (640, 360), Image.Resampling.LANCZOS
    )
    sheet.paste(frame, position)
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (position[0] + 265, position[1] + 370),
        caption,
        font=LABEL,
        fill=(15, 45, 68),
    )

sheet.save(ROOT / "j17a-j20a-a7-a8-b4-b5-alignment-contact-sheet.png")
Image.open(annotated[-1]).save(ROOT / "j17a-j20a-a7-a8-b4-b5-alignment-final.png")
