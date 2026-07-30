"""Render the current-Pro photo-measured proxy and axis scaffold."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


PACKAGE_DIR = Path(__file__).resolve().parent
GATE_DIR = PACKAGE_DIR.parent / "current-lite3-pro-lower-adapter-measurement-gate"
MEASUREMENTS = json.loads((GATE_DIR / "measurement_results.json").read_text(encoding="utf-8"))
RENDER_DIR = PACKAGE_DIR / "renders"

DECK_XY = np.array(
    [
        [20.0, -45.0],
        [20.0, 45.0],
        [5.0, 58.0],
        [-100.0, 70.0],
        [-100.0, -70.0],
        [5.0, -58.0],
    ]
)


def add_dimension(ax, start, end, label, text_offset=(0.0, 0.0), color="#27313d"):
    ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="<->", color=color, lw=1.8))
    midpoint = ((start[0] + end[0]) / 2.0 + text_offset[0], (start[1] + end[1]) / 2.0 + text_offset[1])
    ax.text(*midpoint, label, ha="center", va="center", fontsize=11, color=color, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.9))


def render_top() -> Path:
    fig, ax = plt.subplots(figsize=(14, 9), dpi=150)
    ax.add_patch(Polygon(DECK_XY, closed=True, fc="#eef1f4", ec="#56616d", lw=2.0, label="Photo deck silhouette proxy"))
    ax.add_patch(Rectangle((-300.0, -50.0), 200.0, 100.0, fc="#d7dce2", ec="#697480", lw=2.0, label="Compute enclosure nominal 200 x 100"))
    ax.add_patch(Rectangle((-305.0, -54.0), 209.0, 108.0, fill=False, ec="#d64b43", lw=2.0, ls="--", label="Uncertainty-expanded keep-out"))

    front_axes = [(0.0, 32.5), (0.0, -32.5)]
    for x, y in front_axes:
        ax.add_patch(Circle((x, y), 3.6, fc="#1769d1", ec="white", lw=1.5, zorder=6))
    ax.add_patch(Circle((-75.0, 0.0), 4.0, fc="#f4a40b", ec="white", lw=1.5, zorder=6))
    ax.axvline(20.0, color="#2b9a50", lw=2.0, label="Photo-measured nose edge" )
    ax.axvline(0.0, color="#1769d1", lw=0.9, alpha=0.45)
    ax.axvline(-75.0, color="#f4a40b", lw=0.9, alpha=0.45)
    ax.axvline(-100.0, color="#697480", lw=0.9, alpha=0.55)

    add_dimension(ax, (8.0, -32.5), (8.0, 32.5), "65.0 +/- 1.0 mm", (10.0, 0.0), "#1769d1")
    add_dimension(ax, (0.0, -78.0), (-75.0, -78.0), "75 +/- 3 mm to centre candidate", (0.0, -6.0), "#b87900")
    add_dimension(ax, (0.0, 82.0), (-100.0, 82.0), "100 +/- 4 mm to enclosure front", (0.0, 7.0), "#4c5966")
    add_dimension(ax, (0.0, 66.0), (20.0, 66.0), "20 +/- 2 mm", (0.0, 7.0), "#278b49")

    ax.text(1.5, 39.0, "front small-hole axes\nthread/depth unmeasured", fontsize=10, color="#1252a4")
    ax.text(-73.0, 8.0, "centre visible axis\nreceiver role unverified", fontsize=10, color="#9c6500")
    ax.text(-200.0, 0.0, "compute enclosure\n200 +/- 5 x 100 +/- 4 mm", ha="center", va="center", fontsize=12, color="#3e4852")

    ax.set_title("Current Lite3 Pro - physical photo measurement scaffold (not official CAD)", fontsize=16, pad=16)
    ax.set_xlabel("x: robot forward toward nose (mm)")
    ax.set_ylabel("y: robot left (mm)")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-320.0, 45.0)
    ax.set_ylim(-95.0, 95.0)
    ax.grid(True, color="#e0e4e8", lw=0.7)
    ax.legend(loc="lower left", framealpha=0.96)
    fig.tight_layout()
    output = RENDER_DIR / "01-current-pro-measured-hole-map-top.png"
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output


def box_faces(x0, x1, y0, y1, z0, z1):
    p = np.array(
        [
            [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
            [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
        ]
    )
    return [[p[i] for i in face] for face in ([0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7])]


def add_box(ax, bounds, color, alpha, edge="#4b5662", lw=0.8):
    x0, x1, y0, y1, z0, z1 = bounds
    collection = Poly3DCollection(box_faces(x0,x1,y0,y1,z0,z1), facecolors=color, edgecolors=edge, linewidths=lw, alpha=alpha)
    ax.add_collection3d(collection)


def add_cylinder(ax, x, y, radius, z0, z1, color):
    theta = np.linspace(0.0, 2.0 * np.pi, 36)
    z = np.array([z0, z1])
    tt, zz = np.meshgrid(theta, z)
    xx = x + radius * np.cos(tt)
    yy = y + radius * np.sin(tt)
    ax.plot_surface(xx, yy, zz, color=color, alpha=0.95, linewidth=0.0, shade=True)


def render_isometric() -> Path:
    fig = plt.figure(figsize=(14, 9), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    deck_top = np.c_[DECK_XY, np.zeros(len(DECK_XY))]
    deck_bottom = np.c_[DECK_XY, -4.0 * np.ones(len(DECK_XY))]
    faces = [deck_top, deck_bottom]
    for index in range(len(DECK_XY)):
        nxt = (index + 1) % len(DECK_XY)
        faces.append([deck_bottom[index], deck_bottom[nxt], deck_top[nxt], deck_top[index]])
    ax.add_collection3d(Poly3DCollection(faces, facecolors="#e9edf1", edgecolors="#5d6873", linewidths=0.8, alpha=0.72))
    add_box(ax, (-300,-100,-50,50,0,50), "#d9dee4", 0.84)
    add_box(ax, (-305,-96,-54,54,0,54), "#e35a4f", 0.08, edge="#d64b43", lw=1.1)
    add_cylinder(ax, 0.0, 32.5, 3.2, -5.0, 9.0, "#1769d1")
    add_cylinder(ax, 0.0, -32.5, 3.2, -5.0, 9.0, "#1769d1")
    add_cylinder(ax, -75.0, 0.0, 3.5, -5.0, 9.0, "#f4a40b")
    ax.plot([20,20],[-50,50],[1,1], color="#2b9a50", lw=3.0)
    ax.text(4, 37, 12, "front pair 65 mm", color="#1252a4", fontsize=10)
    ax.text(-76, 5, 12, "centre candidate", color="#9c6500", fontsize=10)
    ax.text(-205, -48, 54, "compute enclosure 200 x 100 x 50", color="#3e4852", fontsize=10)
    ax.set_xlim(-320, 45); ax.set_ylim(-100, 100); ax.set_zlim(-8, 90)
    ax.set_box_aspect((365,200,98))
    ax.view_init(elev=27, azim=-56)
    ax.set_xlabel("x forward"); ax.set_ylabel("y left"); ax.set_zlabel("z up")
    ax.set_title("Current Lite3 Pro photo-measured proxy - layout only, no printable adapter", fontsize=15, pad=18)
    ax.grid(False)
    fig.tight_layout()
    output = RENDER_DIR / "02-current-pro-measured-proxy-isometric.png"
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output


def main() -> None:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [render_top(), render_isometric()]
    print(json.dumps({"outputs": [str(path.relative_to(PACKAGE_DIR)) for path in outputs]}, indent=2))


if __name__ == "__main__":
    main()
