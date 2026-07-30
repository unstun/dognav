from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "mid360-m3-animation-frames"
OUT = ROOT / "mid360-m3-annotated-frames"
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
OUT.mkdir(parents=True, exist_ok=True)

TITLE = ImageFont.truetype(FONT_PATH, 27)
LABEL = ImageFont.truetype(FONT_PATH, 22)
SMALL = ImageFont.truetype(FONT_PATH, 17)
TINY = ImageFont.truetype(FONT_PATH, 15)


def panel(image, xy, fill, outline=None, radius=12, width=2):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(
        xy,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )
    image.alpha_composite(overlay)


def arrow(draw, start, end, color, width=5):
    draw.line([start, end], fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 14
    p1 = (
        end[0] - size * math.cos(angle - math.pi / 6),
        end[1] - size * math.sin(angle - math.pi / 6),
    )
    p2 = (
        end[0] - size * math.cos(angle + math.pi / 6),
        end[1] - size * math.sin(angle + math.pi / 6),
    )
    draw.polygon([end, p1, p2], fill=color)


def annotate(path: Path) -> Path:
    index = int(path.stem.split("_")[-1])
    image = Image.open(path).convert("RGBA")

    if index < 15:
        stage = "1  MID360 与 J20A 分离"
        detail = "四颗橙色螺钉位于支架二下方"
    elif index <= 64:
        stage = "2  MID360 沿安装法向靠近"
        detail = "保持真实 15° 安装方向"
    elif index < 80:
        stage = "3  四孔同轴，安装面贴合"
        detail = "48×36 mm；最大孔轴残差约 2×10⁻¹³ mm"
    elif index <= 129:
        stage = "4  四颗 M3 螺钉从下方拧入"
        detail = "穿过 J20A Ø3.5 通孔，进入 MID360 螺纹孔"
    else:
        stage = "5  终态：MID360 已固定"
        detail = "这一层不加螺母；MID360 本体提供 4×M3 螺纹"

    panel(
        image,
        (14, 14, 435, 211),
        (246, 250, 253, 230),
        (18, 68, 104, 245),
    )
    draw = ImageDraw.Draw(image)
    draw.text(
        (30, 27),
        "J20A → MID360",
        font=TITLE,
        fill=(9, 47, 78, 255),
    )
    draw.text(
        (30, 66),
        "4×M3 下装螺钉连接",
        font=LABEL,
        fill=(9, 47, 78, 255),
    )
    draw.text((30, 105), stage, font=SMALL, fill=(16, 91, 139, 255))
    draw.text((30, 133), detail, font=TINY, fill=(32, 66, 86, 255))
    draw.text(
        (30, 164),
        "橙色：MID360 螺钉　红/绿：已确认的下层连接",
        font=TINY,
        fill=(170, 76, 0, 255),
    )
    draw.text(
        (30, 188),
        "候选 M3×8：J20A 路径 4 mm，建模啮合 4 mm",
        font=TINY,
        fill=(106, 53, 18, 255),
    )

    if 15 <= index <= 64:
        panel(
            image,
            (920, 42, 1254, 107),
            (231, 247, 255, 225),
            (0, 126, 196, 240),
        )
        draw = ImageDraw.Draw(image)
        draw.text(
            (942, 58),
            "MID360 向安装面落位",
            font=SMALL,
            fill=(0, 83, 133, 255),
        )
        arrow(draw, (1000, 122), (890, 244), (0, 126, 196, 255), 5)
    elif 65 <= index < 80:
        panel(
            image,
            (905, 42, 1254, 107),
            (229, 250, 235, 228),
            (19, 158, 78, 245),
        )
        draw = ImageDraw.Draw(image)
        draw.text(
            (934, 58),
            "4 个孔轴已经一一重合",
            font=SMALL,
            fill=(11, 111, 48, 255),
        )
    elif 80 <= index <= 129:
        panel(
            image,
            (885, 42, 1254, 107),
            (255, 242, 218, 232),
            (245, 133, 0, 245),
        )
        draw = ImageDraw.Draw(image)
        draw.text(
            (909, 58),
            "橙色螺钉从支架下方进入",
            font=SMALL,
            fill=(153, 74, 0, 255),
        )
        arrow(draw, (1058, 520), (1015, 405), (245, 133, 0, 255), 5)
    elif index > 129:
        panel(
            image,
            (882, 42, 1254, 107),
            (229, 250, 235, 232),
            (19, 158, 78, 245),
        )
        draw = ImageDraw.Draw(image)
        draw.text(
            (906, 58),
            "4 颗螺钉已进入 MID360",
            font=SMALL,
            fill=(11, 111, 48, 255),
        )

    destination = OUT / path.name
    image.convert("RGB").save(destination, quality=95)
    return destination


raw_frames = sorted(RAW.glob("frame_*.png"))
if len(raw_frames) != 160:
    raise RuntimeError(f"Expected 160 raw frames, found {len(raw_frames)}")

annotated = [annotate(path) for path in raw_frames]

selected = [
    (0, "分离"),
    (38, "MID360 靠近"),
    (72, "四孔重合"),
    (85, "螺钉开始上行"),
    (112, "螺钉进入"),
    (159, "安装终态"),
]
sheet = Image.new("RGB", (1920, 820), "white")
positions = [(0, 0), (640, 0), (1280, 0), (0, 410), (640, 410), (1280, 410)]
for (frame_index, caption), position in zip(selected, positions):
    frame = Image.open(annotated[frame_index]).convert("RGB").resize(
        (640, 360),
        Image.Resampling.LANCZOS,
    )
    sheet.paste(frame, position)
    draw = ImageDraw.Draw(sheet)
    box = draw.textbbox((0, 0), caption, font=LABEL)
    text_width = box[2] - box[0]
    draw.text(
        (position[0] + (640 - text_width) // 2, position[1] + 370),
        caption,
        font=LABEL,
        fill=(15, 45, 68),
    )

sheet.save(ROOT / "j20a-mid360-4xm3-installation-contact-sheet.png")
Image.open(annotated[-1]).save(ROOT / "j20a-mid360-4xm3-installed-final.png")
