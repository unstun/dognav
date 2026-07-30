from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT = ImageFont.truetype(FONT_PATH, 21)
TITLE = ImageFont.truetype(FONT_PATH, 31)
NOTE = ImageFont.truetype(FONT_PATH, 22)


J17_HOLES = [
    ("A1", 541, 41),
    ("A2", 739, 41),
    ("A3", 497, 90),
    ("A4", 783, 90),
    ("A5", 450, 121),
    ("A6", 535, 108),
    ("A7", 560, 133),
    ("A8", 719, 133),
    ("A9", 744, 108),
    ("A10", 829, 121),
    ("A11", 441, 329),
    ("A12", 839, 329),
    ("A13", 490, 478),
    ("A14", 790, 478),
    ("A15", 450, 606),
    ("A16", 829, 606),
    ("A17", 408, 681),
    ("A18", 871, 681),
]

J20_HOLES = [
    ("B1", 466, 64),
    ("B2", 813, 64),
    ("B3", 503, 76),
    ("B4", 513, 107),
    ("B5", 766, 107),
    ("B6", 513, 185),
    ("B7", 766, 185),
    ("B8", 513, 511),
    ("B9", 766, 511),
    ("B10", 503, 624),
    ("B11", 861, 624),
    ("B12", 465, 636),
    ("B13", 815, 636),
    ("B14", 401, 659),
    ("B15", 879, 659),
]


def label_panel(source: str, output: str, title: str, holes, color):
    raw = Image.open(ROOT / source).convert("RGBA")
    canvas = Image.new("RGBA", (1280, 800), (247, 249, 252, 255))
    canvas.paste(raw, (0, 80))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((16, 12, 1264, 66), radius=15, fill=(20, 42, 68, 238))
    draw.text((36, 20), title, font=TITLE, fill="white")
    for label, x, y in holes:
        y += 80
        r = 17
        draw.ellipse((x - r, y - r, x + r, y + r), outline=color, width=5)
        tx = x + 13
        ty = y - 34
        box = draw.textbbox((tx, ty), label, font=FONT)
        draw.rounded_rectangle((box[0] - 4, box[1] - 2, box[2] + 4, box[3] + 2), radius=6, fill=(*color[:3], 225))
        draw.text((tx, ty), label, font=FONT, fill=(10, 20, 25, 255))
    canvas.convert("RGB").save(ROOT / output)


label_panel(
    "raw-j17-front.png",
    "j17-hole-map-all-yellow.png",
    "支架一 J17A：全部可见候选孔（黄色，A1–A18）",
    J17_HOLES,
    (255, 205, 0, 255),
)
label_panel(
    "raw-j20-front.png",
    "j20-hole-map-all-blue.png",
    "支架二 J20A：全部可见候选孔（蓝色，B1–B15）",
    J20_HOLES,
    (30, 155, 255, 255),
)


overlay_raw = Image.open(ROOT / "raw-overlay-front.png").convert("RGBA")
overlay = Image.new("RGBA", (1280, 800), (247, 249, 252, 255))
overlay.paste(overlay_raw, (0, 80))
draw = ImageDraw.Draw(overlay)
draw.rounded_rectangle((16, 12, 1264, 66), radius=15, fill=(20, 42, 68, 238))
draw.text((36, 20), "两支架叠合、不装螺钉：请确认真正的前端连接孔", font=TITLE, fill="white")

for x, y in ((560, 133), (719, 133)):
    y += 80
    draw.ellipse((x - 24, y - 24, x + 24, y + 24), outline=(245, 45, 45, 255), width=7)
draw.rounded_rectangle((42, 100, 430, 145), radius=10, fill=(255, 238, 238, 238), outline=(245, 45, 45, 255), width=3)
draw.text((60, 108), "我刚才选的前端孔：A7/A8 ↔ B4/B5", font=NOTE, fill=(165, 20, 20, 255))

for x, y in ((490, 478), (790, 478)):
    y += 80
    draw.ellipse((x - 29, y - 29, x + 29, y + 29), outline=(0, 155, 92, 255), width=7)
draw.rounded_rectangle((810, 540, 1240, 585), radius=10, fill=(228, 250, 239, 238), outline=(0, 155, 92, 255), width=3)
draw.text((828, 548), "后端已使用孔：A13/A14 ↔ B12/B13", font=NOTE, fill=(0, 105, 62, 255))
overlay.convert("RGB").save(ROOT / "overlay-hole-map-current-assumption.png")


side_raw = Image.open(ROOT / "raw-overlay-side.png").convert("RGBA")
side = Image.new("RGBA", (1280, 800), (247, 249, 252, 255))
side.paste(side_raw, (0, 80))
draw = ImageDraw.Draw(side)
draw.rounded_rectangle((16, 12, 1264, 66), radius=15, fill=(20, 42, 68, 238))
draw.text((36, 20), "侧视图：仅仅“投影同轴”还不能替代真实夹紧关系确认", font=TITLE, fill="white")
draw.ellipse((625, 135, 730, 245), outline=(245, 45, 45, 255), width=7)
draw.text((750, 163), "前端候选区域", font=NOTE, fill=(165, 20, 20, 255))
draw.ellipse((565, 500, 710, 625), outline=(0, 155, 92, 255), width=7)
draw.text((735, 535), "后端已使用区域", font=NOTE, fill=(0, 105, 62, 255))
side.convert("RGB").save(ROOT / "overlay-side-contact-check.png")


panels = [
    Image.open(ROOT / "j17-hole-map-all-yellow.png").convert("RGB"),
    Image.open(ROOT / "j20-hole-map-all-blue.png").convert("RGB"),
    Image.open(ROOT / "overlay-hole-map-current-assumption.png").convert("RGB"),
    Image.open(ROOT / "overlay-side-contact-check.png").convert("RGB"),
]
sheet = Image.new("RGB", (1920, 1200), "white")
for index, panel in enumerate(panels):
    panel = panel.resize((960, 600), Image.Resampling.LANCZOS)
    sheet.paste(panel, ((index % 2) * 960, (index // 2) * 600))
sheet.save(ROOT / "j17-j20-hole-mapping-review-sheet.png")
