"""Create a review sheet showing how the photo-measured scaffold was read."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps


PACKAGE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = (
    PACKAGE_DIR.parent
    / "current-lite3-pro-lower-adapter-measurement-gate"
    / "source/2026-07-30-user-physical-measurements"
)
OUTPUT = PACKAGE_DIR / "renders/00-physical-measurement-evidence-sheet.jpg"


def load(name: str) -> np.ndarray:
    return np.asarray(ImageOps.exif_transpose(Image.open(SOURCE_DIR / name)).convert("RGB"))


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(16, 11), dpi=150)

    pitch = load("photo-09.jpg")
    ax = axes[0, 0]
    ax.imshow(pitch)
    left = (375, 418)
    right = (704, 476)
    ax.scatter([left[0], right[0]], [left[1], right[1]], s=170, facecolors="none", edgecolors="#1769d1", linewidths=3)
    ax.annotate("", xy=right, xytext=left, arrowprops=dict(arrowstyle="<->", color="#1769d1", lw=3))
    ax.text(535, 360, "65.0 +/- 1.0 mm centre pitch", ha="center", color="#0e4f9f", fontsize=14, bbox=dict(fc="white", ec="none", alpha=0.88))
    ax.set_title("A. Two front small-hole axes (best lateral view)", fontsize=14)
    ax.set_axis_off()

    longitudinal = np.rot90(load("photo-07.jpg"), k=3)
    ax = axes[0, 1]
    ax.imshow(longitudinal)
    lines = [
        (385, "nose edge  +20 mm", "#2b9a50"),
        (450, "front row  x = 0", "#1769d1"),
        (725, "centre visible axis  x ~= -75 mm", "#f0a000"),
        (820, "compute enclosure front  x ~= -100 mm", "#4c5966"),
    ]
    for y, label, color in lines:
        ax.hlines(y, 380, 1010, color=color, lw=3)
        ax.text(1030, y, label, va="center", color=color, fontsize=12, bbox=dict(fc="white", ec="none", alpha=0.82))
    ax.set_xlim(260, 1440)
    ax.set_ylim(1020, 270)
    ax.set_title("B. Longitudinal datum scaffold", fontsize=14)
    ax.set_axis_off()

    height = load("photo-04.jpg")
    ax = axes[1, 0]
    ax.imshow(height)
    deck_y = 1175
    top_y = 655
    ax.hlines([deck_y, top_y], 720, 1350, colors=["#2b9a50", "#4c5966"], linewidths=3)
    ax.annotate("", xy=(1230, top_y), xytext=(1230, deck_y), arrowprops=dict(arrowstyle="<->", color="#8a3fc7", lw=3))
    ax.text(1280, (deck_y + top_y) / 2, "50 +/- 2 mm\nphoto envelope height", va="center", color="#6b2e9c", fontsize=14, bbox=dict(fc="white", ec="none", alpha=0.87))
    ax.set_xlim(580, 1500)
    ax.set_ylim(1260, 500)
    ax.set_title("C. Compute enclosure height from local deck plane", fontsize=14)
    ax.set_axis_off()

    width = np.rot90(load("photo-05.jpg"), k=3)
    ax = axes[1, 1]
    ax.imshow(width)
    left_x = 515
    right_x = 950
    y = 520
    ax.vlines([left_x, right_x], 500, 720, colors="#4c5966", linewidths=3)
    ax.annotate("", xy=(right_x, y), xytext=(left_x, y), arrowprops=dict(arrowstyle="<->", color="#4c5966", lw=3))
    ax.text((left_x + right_x) / 2, 475, "100 +/- 4 mm external width", ha="center", color="#3e4852", fontsize=14, bbox=dict(fc="white", ec="none", alpha=0.87))
    ax.set_xlim(330, 1130)
    ax.set_ylim(800, 350)
    ax.set_title("D. Compute enclosure transverse envelope", fontsize=14)
    ax.set_axis_off()

    fig.suptitle("Current Lite3 Pro physical measurement evidence - photo estimates, not manufacturing dimensions", fontsize=18, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUTPUT, pil_kwargs={"quality": 94}, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
