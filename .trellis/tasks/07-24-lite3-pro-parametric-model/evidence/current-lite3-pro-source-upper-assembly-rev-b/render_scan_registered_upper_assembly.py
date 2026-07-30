#!/usr/bin/env python3
"""Render the scan-registered two-recess body with the source upper stack."""

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
FCSTD_PATH = PACKAGE_DIR / "cad/current-lite3-pro-source-upper-assembly-rev-b.FCStd"
VALIDATION_PATH = PACKAGE_DIR / "validation.json"
RENDER_DIR = PACKAGE_DIR / "renders"
FONT_PATH = Path("/System/Library/Fonts/STHeiti Light.ttc")
if FONT_PATH.exists():
    FONT_NAME = font_manager.FontProperties(fname=str(FONT_PATH)).get_name()
    matplotlib.rcParams["font.family"] = FONT_NAME
matplotlib.rcParams["axes.unicode_minus"] = False

STYLE = {
    "ComputeEnclosureScanNominal": ("#d9dde4", 0.72, "#545b65", 0.08),
    "DeckPlanarProxy": ("#eef0f4", 0.32, "#a4aab3", 0.03),
    "J20ASourceBRep": ("#c9b995", 1.0, "#4d4638", 0.04),
    "S410SourceBRep": ("#30343a", 1.0, "#14171a", 0.04),
    "Mid360OfficialBRep": ("#4169a8", 1.0, "#1e3558", 0.025),
    "FrontLeftAxis": ("#1a6ce0", 1.0, "#0b3979", 0.05),
    "FrontRightAxis": ("#1a6ce0", 1.0, "#0b3979", 0.05),
    "CentreCandidateAxis": ("#f4a90d", 1.0, "#8a5a00", 0.05),
    "UsableNoseEdge": ("#1eb457", 1.0, "#0b6330", 0.05),
}


def triangles(shape, tolerance=0.75):
    vertices, indices = shape.tessellate(tolerance)
    points = np.asarray([[vertex.x, vertex.y, vertex.z] for vertex in vertices])
    return points[np.asarray(indices, dtype=int)]


def add_shape(ax, shape, style):
    color, alpha, edge, linewidth = style
    ax.add_collection3d(
        Poly3DCollection(
            triangles(shape),
            facecolors=color,
            edgecolors=edge,
            linewidths=linewidth,
            alpha=alpha,
            rasterized=True,
        )
    )


def add_keepout_wireframe(ax, bounds):
    x0, y0, z0 = bounds["min"]
    x1, y1, z1 = bounds["max"]
    corners = np.asarray(
        [
            [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
            [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
        ]
    )
    for a, b in (
        (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ):
        ax.plot(*zip(corners[a], corners[b]), color="#d9443d", linewidth=1.0, alpha=0.55)


def configure(ax, title, elev, azim):
    ax.set_xlim(-315, 35)
    ax.set_ylim(-75, 75)
    ax.set_zlim(-5, 112)
    ax.set_box_aspect((350, 150, 117))
    ax.set_xlabel("x 向前 (mm)")
    ax.set_ylabel("y 向左 (mm)")
    ax.set_zlabel("z 向上 (mm)")
    if elev >= 80:
        ax.set_zticks([])
        ax.set_zlabel("")
    ax.view_init(elev=elev, azim=azim)
    ax.set_proj_type("ortho")
    ax.set_title(title, fontsize=15, pad=16)
    ax.grid(False)


def render(document, validation, filename, title, elev, azim):
    fig = plt.figure(figsize=(15, 8.5), dpi=170)
    ax = fig.add_subplot(111, projection="3d")
    for name, style in STYLE.items():
        add_shape(ax, document.getObject(name).Shape, style)
    keepout_bounds = validation["geometry"]["compute_enclosure_scan_nominal"]["bounds_mm"]
    expanded = document.getObject("ExpandedComputeKeepout").Shape.BoundBox
    add_keepout_wireframe(
        ax,
        {"min": [expanded.XMin, expanded.YMin, expanded.ZMin], "max": [expanded.XMax, expanded.YMax, expanded.ZMax]},
    )
    ax.text(-116, -67, 52, "两侧内凹台阶", color="#30343a", fontsize=11, weight="bold")
    ax.text(-44, 0, 104, "MID-360 + S410", color="#26384d", fontsize=11, weight="bold")
    ax.text(-302, -70, 58, "红线：保守碰撞禁入区", color="#b8342e", fontsize=9)
    configure(ax, title, elev, azim)
    fig.text(
        0.5,
        0.025,
        "灰色实体：扫描修正后的双凹口工控机外形；红线：仍按完整长方体保守避碰；尚未定义机身螺纹与下层承力连接",
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
        raise RuntimeError("Refusing to render a non-passing assembly")
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    document = App.openDocument(str(FCSTD_PATH))
    outputs = [
        render(
            document,
            validation,
            "01-scan-registered-upper-top.png",
            "Lite3 专业版扫描注册总装审查：双凹口俯视",
            88,
            -90,
        ),
        render(
            document,
            validation,
            "02-scan-registered-upper-isometric.png",
            "Lite3 专业版扫描注册总装审查：双凹口与上层总成",
            24,
            -62,
        ),
    ]
    App.closeDocument(document.Name)
    print(json.dumps({"outputs": [str(path.relative_to(PACKAGE_DIR)) for path in outputs]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
