from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "front-m3-animation-frames"
OUT = ROOT / "front-m3-annotated-frames"
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int):
    return ImageFont.truetype(FONT_PATH, size)


TITLE = font(34)
LABEL = font(26)
SMALL = font(20)
TINY = font(17)


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


def translucent_box(image, xy, fill, outline=None, radius=14, width=2):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    image.alpha_composite(overlay)


def annotate(path: Path):
    idx = int(path.stem.split("_")[-1])
    image = Image.open(path).convert("RGBA")
    draw = ImageDraw.Draw(image)

    translucent_box(image, (18, 14, 1010, 66), (14, 31, 55, 218), (58, 174, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text(
        (38, 20),
        "支架一 + 支架二：前端 M3 与后端 M4 的完整固定",
        font=TITLE,
        fill=(255, 255, 255, 255),
    )

    if idx < 14:
        progress = 0.0
        stage = "1  前端两颗 M3 对准左右匹配孔"
    elif idx <= 64:
        progress = ease((idx - 14) / 50.0)
        stage = "2  从支架一下方旋入支架二的 2×M3 螺纹孔"
    else:
        progress = 1.0
        stage = "3  前端 M3 + 后端 M4：前后四点固定完成"

    translucent_box(image, (20, 552, 1015, 706), (250, 250, 250, 225), (25, 65, 95, 230))
    draw = ImageDraw.Draw(image)
    draw.text((40, 564), stage, font=LABEL, fill=(14, 46, 74, 255))
    draw.rounded_rectangle((42, 611, 66, 635), radius=5, fill=(255, 82, 0, 255))
    draw.text((78, 606), "红色：前端 2×M3 螺钉，穿过 J17A 后拧入 J20A", font=SMALL, fill=(30, 30, 30, 255))
    draw.rounded_rectangle((42, 649, 66, 673), radius=5, fill=(247, 202, 24, 255))
    draw.text((78, 644), "黄/青/绿：后端原有 M4 螺栓、垫圈与锁紧件演示", font=SMALL, fill=(30, 30, 30, 255))
    draw.text(
        (40, 681),
        "CAD 已确认前端为 2×M3；M3×6 是按当前孔深给出的演示候选，实物选型仍需复核板厚与有效啮合。",
        font=TINY,
        fill=(100, 42, 20, 255),
    )

    a0, a1 = (461, 139), (548, 174)
    b0, b1 = (563, 67), (649, 76)
    pa = (round(a0[0] + (a1[0] - a0[0]) * progress), round(a0[1] + (a1[1] - a0[1]) * progress))
    pb = (round(b0[0] + (b1[0] - b0[0]) * progress), round(b0[1] + (b1[1] - b0[1]) * progress))

    for p in (pa, pb):
        draw.ellipse((p[0] - 24, p[1] - 24, p[0] + 24, p[1] + 24), outline=(255, 62, 0, 255), width=4)

    if idx <= 64:
        arrow(draw, (370, 92), pa, (255, 82, 0, 255), 5)
        draw.text((95, 78), "前端两颗 M3 同步旋入", font=LABEL, fill=(196, 48, 0, 255))
    else:
        draw.rounded_rectangle((870, 86, 1238, 126), radius=10, fill=(222, 250, 229, 235), outline=(28, 140, 75, 255), width=3)
        draw.text((890, 92), "前端已锁紧", font=LABEL, fill=(14, 95, 48, 255))
        arrow(draw, (1000, 126), (649, 76), (28, 140, 75, 255), 4)
        draw.ellipse((526, 535, 588, 597), outline=(255, 185, 0, 255), width=4)
        draw.ellipse((805, 437, 867, 499), outline=(255, 185, 0, 255), width=4)
        draw.text((886, 432), "后端两组固定保留", font=SMALL, fill=(132, 88, 0, 255))

    dest = OUT / path.name
    image.convert("RGB").save(dest, quality=95)
    return dest


paths = sorted(RAW.glob("frame_*.png"))
if len(paths) != 84:
    raise RuntimeError(f"Expected 84 raw frames, found {len(paths)}")

annotated = [annotate(path) for path in paths]

sheet = Image.new("RGB", (1920, 420), "white")
for column, idx in enumerate((0, 42, 83)):
    frame = Image.open(annotated[idx]).convert("RGB").resize((640, 360), Image.Resampling.LANCZOS)
    sheet.paste(frame, (640 * column, 0))
    sd = ImageDraw.Draw(sheet)
    caption = ("对准", "旋入", "前后四点锁紧")[column]
    sd.text((640 * column + 265, 372), caption, font=LABEL, fill=(15, 43, 67))

sheet.save(ROOT / "j17a-j20a-front-m3-complete-fastening-contact-sheet.png")
Image.open(annotated[-1]).save(ROOT / "j17a-j20a-front-m3-complete-fastening-final.png")
