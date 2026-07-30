#!/usr/bin/env python3
"""Render the scan Rev B D435i collision/support study."""

from __future__ import annotations

import json
from pathlib import Path

import FreeCAD as App
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


PACKAGE_DIR = Path(__file__).resolve().parent
FCSTD_PATH = PACKAGE_DIR / "cad/current-lite3-pro-d435i-support-study-rev-b.FCStd"
VALIDATION_PATH = PACKAGE_DIR / "validation.json"
RENDER_DIR = PACKAGE_DIR / "renders"
FONT_PATH = Path("/System/Library/Fonts/STHeiti Light.ttc")
if FONT_PATH.exists():
    matplotlib.rcParams["font.family"] = font_manager.FontProperties(
        fname=str(FONT_PATH)
    ).get_name()
matplotlib.rcParams["axes.unicode_minus"] = False

STYLE = {
    "ComputeEnclosureScanNominal": ("#d9dde4", 0.52, "#59616b", 0.05),
    "DeckPlanarProxy": ("#eef0f4", 0.22, "#a4aab3", 0.02),
    "J20aReview": ("#c9b995", 0.94, "#4d4638", 0.025),
    "S410Review": ("#30343a", 0.94, "#14171a", 0.025),
    "Mid360Review": ("#4169a8", 0.92, "#1e3558", 0.018),
    "D435iSupportCandidate": ("#e29228", 1.0, "#7d4707", 0.08),
    "D435iOfficialEnvelope": ("#91a2b4", 0.38, "#3f5367", 0.05),
}


def triangles(shape, tolerance=0.75):
    vertices, indices = shape.tessellate(tolerance)
    points = np.asarray([[vertex.x, vertex.y, vertex.z] for vertex in vertices])
    return points[np.asarray(indices, dtype=int)]


def add_shape(ax, shape, style):
    color, alpha, edge, linewidth = style
    ax.add_collection3d(
        Poly3DCollection(
            triangles(shape), facecolors=color, edgecolors=edge,
            linewidths=linewidth, alpha=alpha, rasterized=True,
        )
    )


def add_keepout_wireframe(ax, shape):
    box = shape.BoundBox
    corners = np.asarray(
        [
            [box.XMin, box.YMin, box.ZMin], [box.XMax, box.YMin, box.ZMin],
            [box.XMax, box.YMax, box.ZMin], [box.XMin, box.YMax, box.ZMin],
            [box.XMin, box.YMin, box.ZMax], [box.XMax, box.YMin, box.ZMax],
            [box.XMax, box.YMax, box.ZMax], [box.XMin, box.YMax, box.ZMax],
        ]
    )
    for a, b in (
        (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ):
        ax.plot(*zip(corners[a], corners[b]), color="#d9443d", linewidth=0.9, alpha=0.45)


def render(document, validation, filename, title, elev, azim):
    fig = plt.figure(figsize=(15, 8.5), dpi=170)
    ax = fig.add_subplot(111, projection="3d")
    for name, style in STYLE.items():
        add_shape(ax, document.getObject(name).Shape, style)
    add_keepout_wireframe(ax, document.getObject("ExpandedComputeKeepout").Shape)
    ax.set_xlim(-315, 55)
    ax.set_ylim(-75, 75)
    ax.set_zlim(-5, 112)
    ax.set_box_aspect((370, 150, 117))
    ax.set_xlabel("x 向前 (mm)")
    ax.set_ylabel("y 向左 (mm)")
    ax.set_zlabel("z 向上 (mm)")
    ax.view_init(elev=elev, azim=azim)
    ax.set_proj_type("ortho")
    ax.set_title(title, fontsize=15, pad=16)
    ax.grid(False)
    ax.text(30, -47, 44, "D435i 名义碰撞包络", color="#33485c", fontsize=10, weight="bold")
    ax.text(7, -35, 8, "橙色：一体支撑候选", color="#9b5708", fontsize=10, weight="bold")
    ax.text(-46, 2, 102, "MID-360 + S410", color="#26384d", fontsize=10, weight="bold")
    fig.text(
        0.5,
        0.025,
        "几何检查：支撑为 1 个实体；D435i 后部两孔中心距 45 mm；与相机、上层总成及扫描禁入区均无正体积穿模。下层机身连接仍未定义。",
        ha="center",
        fontsize=10,
        color="#343b44",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    output = RENDER_DIR / filename
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output


def main() -> None:
    validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    if not validation.get("pass"):
        raise RuntimeError("Refusing to render a non-passing study")
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    document = App.openDocument(str(FCSTD_PATH))
    outputs = [
        render(document, validation, "01-d435i-support-isometric.png", "Lite3 专业版扫描注册传感器总装：D435i 支撑审查", 22, -58),
        render(document, validation, "02-d435i-support-side.png", "D435i 先装顺序与 20° 下倾侧视", 2, -90),
    ]
    App.closeDocument(document.Name)
    print(json.dumps({"outputs": [str(path.relative_to(PACKAGE_DIR)) for path in outputs]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
