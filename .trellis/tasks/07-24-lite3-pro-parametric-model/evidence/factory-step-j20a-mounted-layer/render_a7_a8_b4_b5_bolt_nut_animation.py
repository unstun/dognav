from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "a7-a8-b4-b5-bolt-nut-animation-frames"
OUT = ROOT / "a7-a8-b4-b5-bolt-nut-annotated-frames"
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
OUT.mkdir(parents=True, exist_ok=True)

TITLE = ImageFont.truetype(FONT_PATH, 31)
LABEL = ImageFont.truetype(FONT_PATH, 24)
SMALL = ImageFont.truetype(FONT_PATH, 18)
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
    panel(image, (18, 14, 1145, 64), (14, 34, 58, 224), (65, 181, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text(
        (36, 20),
        "A7/A8 ↔ B4/B5：贯穿螺栓 + 支架二远侧螺母",
        font=TITLE,
        fill="white",
    )

    if index < 15:
        stage = "1  支架一 A7/A8 与支架二 B4/B5 保持分离"
        bracket_progress = 0.0
    elif index <= 59:
        stage = "2  支架二靠近：B4 → A7，B5 → A8"
        bracket_progress = ease((index - 15) / 44.0)
    elif index < 75:
        stage = "3  蓝环套入黄环：两组孔中心重合"
        bracket_progress = 1.0
    elif index <= 115:
        stage = "4  两颗红色贯穿螺栓从支架一下方穿入"
        bracket_progress = 1.0
    elif index < 126:
        stage = "5  螺栓已穿过支架一和支架二，等待远侧螺母"
        bracket_progress = 1.0
    elif index <= 170:
        stage = "6  两颗绿色六角螺母从支架二远侧落位并旋紧"
        bracket_progress = 1.0
    else:
        stage = "7  终态：两颗贯穿螺栓 + 两颗上侧螺母"
        bracket_progress = 1.0

    panel(image, (18, 552, 1200, 707), (250, 251, 252, 232), (25, 63, 92, 235))
    draw = ImageDraw.Draw(image)
    draw.text((38, 564), stage, font=LABEL, fill=(12, 48, 77, 255))
    legend = [
        ((255, 205, 0), "黄色：支架一 A7/A8", 40),
        ((0, 140, 255), "蓝色：支架二 B4/B5", 305),
        ((245, 50, 25), "红色：2×贯穿螺栓", 610),
        ((20, 220, 70), "绿色：2×远侧螺母", 875),
    ]
    for color, text, x in legend:
        draw.rounded_rectangle((x, 608, x + 24, 632), radius=5, fill=(*color, 255))
        draw.text((x + 34, 603), text, font=SMALL, fill=(25, 25, 25, 255))
    draw.text(
        (40, 646),
        "轴向检查：B4/B5 可贯通；螺母坐在 J20A 远侧表面，而不是悬空放置。",
        font=SMALL,
        fill=(30, 86, 54, 255),
    )
    draw.text(
        (40, 675),
        "M3×12 与缩放六角螺母是装配演示候选；最终标准件、扭矩和承载仍需实物复核。",
        font=TINY,
        fill=(94, 47, 24, 255),
    )

    yellow = [(565, 159), (684, 192)]
    blue_start = [(628, 115), (747, 147)]
    blue = [
        (
            round(start[0] + (end[0] - start[0]) * bracket_progress),
            round(start[1] + (end[1] - start[1]) * bracket_progress),
        )
        for start, end in zip(blue_start, yellow)
    ]

    if index <= 59:
        for source, target in zip(blue, yellow):
            draw.ellipse(
                (source[0] - 20, source[1] - 20, source[0] + 20, source[1] + 20),
                outline=(0, 140, 255, 255),
                width=4,
            )
            arrow(draw, source, target, (0, 140, 255, 255), 4)
    elif 60 <= index < 75:
        for point in yellow:
            draw.ellipse(
                (point[0] - 25, point[1] - 25, point[0] + 25, point[1] + 25),
                outline=(25, 175, 82, 255),
                width=6,
            )

    if 126 <= index <= 170:
        nut_progress = ease((index - 126) / 44.0)
        starts = [(625, 116), (744, 148)]
        targets = [(574, 148), (693, 181)]
        for start, target in zip(starts, targets):
            point = (
                round(start[0] + (target[0] - start[0]) * nut_progress),
                round(start[1] + (target[1] - start[1]) * nut_progress),
            )
            draw.ellipse(
                (point[0] - 22, point[1] - 22, point[0] + 22, point[1] + 22),
                outline=(20, 205, 70, 255),
                width=5,
            )
            arrow(draw, point, target, (20, 175, 65, 255), 4)
        draw.text((860, 108), "绿色螺母旋到远侧", font=LABEL, fill=(10, 125, 48, 255))
    elif index > 170:
        draw.rounded_rectangle(
            (840, 100, 1230, 148),
            radius=10,
            fill=(224, 250, 232, 238),
            outline=(20, 160, 65, 255),
            width=3,
        )
        draw.text((860, 108), "两颗螺母已锁紧", font=LABEL, fill=(10, 112, 45, 255))

    destination = OUT / path.name
    image.convert("RGB").save(destination, quality=95)
    return destination


raw_frames = sorted(RAW.glob("frame_*.png"))
if len(raw_frames) != 185:
    raise RuntimeError(f"Expected 185 raw frames, found {len(raw_frames)}")
annotated = [annotate(path) for path in raw_frames]

selected = [
    (0, "分离"),
    (38, "支架二靠近"),
    (70, "孔位重合"),
    (100, "贯穿螺栓穿入"),
    (148, "螺母旋紧"),
    (184, "终态"),
]
sheet = Image.new("RGB", (1920, 820), "white")
positions = [(0, 0), (640, 0), (1280, 0), (0, 410), (640, 410), (1280, 410)]
for (frame_index, caption), position in zip(selected, positions):
    frame = Image.open(annotated[frame_index]).convert("RGB").resize(
        (640, 360), Image.Resampling.LANCZOS
    )
    sheet.paste(frame, position)
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (position[0] + 250, position[1] + 370),
        caption,
        font=LABEL,
        fill=(15, 45, 68),
    )

sheet.save(ROOT / "j17a-j20a-a7-a8-b4-b5-bolt-nut-contact-sheet.png")
Image.open(annotated[-1]).save(ROOT / "j17a-j20a-a7-a8-b4-b5-bolt-nut-final.png")
