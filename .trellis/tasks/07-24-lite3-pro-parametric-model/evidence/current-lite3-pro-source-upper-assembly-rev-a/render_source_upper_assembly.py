#!/usr/bin/env python3
"""Render the source-backed compact upper assembly from its FCStd shapes."""

from __future__ import annotations

import json
from pathlib import Path

import FreeCAD as App
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


PACKAGE_DIR = Path(__file__).resolve().parent
FCSTD_PATH = PACKAGE_DIR / "cad/current-lite3-pro-source-upper-assembly-rev-a.FCStd"
VALIDATION_PATH = PACKAGE_DIR / "validation.json"
RENDER_DIR = PACKAGE_DIR / "renders"

COLORS = {
    "J20ASourceBRep": "#c9b995",
    "S410SourceBRep": "#30343a",
    "Mid360OfficialBRep": "#4169a8",
}


def triangles(shape, tolerance=0.7):
    vertices, indices = shape.tessellate(tolerance)
    points = np.asarray([[vertex.x, vertex.y, vertex.z] for vertex in vertices])
    return points[np.asarray(indices, dtype=int)]


def add_shape(ax, shape, color, alpha=1.0, edge="#20252a", linewidth=0.04):
    collection = Poly3DCollection(
        triangles(shape),
        facecolors=color,
        edgecolors=edge,
        linewidths=linewidth,
        alpha=alpha,
        rasterized=True,
    )
    ax.add_collection3d(collection)


def add_boundary_plane(ax, x, y0, y1, z0, z1, color, alpha):
    face = [
        [x, y0, z0],
        [x, y1, z0],
        [x, y1, z1],
        [x, y0, z1],
    ]
    ax.add_collection3d(
        Poly3DCollection([face], facecolors=color, edgecolors=color, alpha=alpha)
    )


def configure(ax, title, elev, azim):
    ax.set_xlim(-110, 35)
    ax.set_ylim(-70, 70)
    ax.set_zlim(0, 112)
    ax.set_box_aspect((145, 140, 112))
    ax.set_xlabel("x forward (mm)")
    ax.set_ylabel("y left (mm)")
    ax.set_zlabel("z up (mm)")
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title, fontsize=15, pad=18)
    ax.grid(False)


def render(document, validation, filename, title, elev, azim, side_view=False):
    fig = plt.figure(figsize=(13, 9), dpi=160)
    ax = fig.add_subplot(111, projection="3d")
    for name, color in COLORS.items():
        add_shape(ax, document.getObject(name).Shape, color)
    add_boundary_plane(ax, -96.0, -57.5, 57.5, 0.0, 105.0, "#d94a43", 0.12)
    add_boundary_plane(ax, 20.0, -57.5, 57.5, 0.0, 105.0, "#2c9a51", 0.10)
    ax.text(-50, -3, 13, "J20A", color="#5d4e31", fontsize=11, weight="bold")
    ax.text(-35, 0, 69, "MID-360", color="#244579", fontsize=11, weight="bold")
    ax.text(-58, 50, 87, "S410", color="#1f2226", fontsize=11, weight="bold")
    ax.text(-96, -65, 3, "compute keep-out boundary", color="#b6322c", fontsize=9)
    ax.text(20, -60, 3, "measured nose edge", color="#247c43", fontsize=9)
    configure(ax, title, elev, azim)
    if side_view:
        ax.set_yticks([])
        ax.set_ylabel("")
    fig.text(
        0.5,
        0.025,
        "Source axes registered; rear clearance %.1f mm, front clearance %.1f mm; no lower adapter or print release"
        % (
            validation["clearance_mm"][
                "combined_upper_to_expanded_compute_keepout_x"
            ],
            validation["clearance_mm"]["combined_front_to_measured_nose_edge"],
        ),
        ha="center",
        fontsize=10,
        color="#39424c",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    output = RENDER_DIR / filename
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output


def main() -> None:
    if not FCSTD_PATH.exists() or not VALIDATION_PATH.exists():
        raise FileNotFoundError("Build and validate the source upper assembly first")
    validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    if not validation.get("pass"):
        raise RuntimeError("Refusing to render a non-passing assembly")
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    document = App.openDocument(str(FCSTD_PATH))
    outputs = [
        render(
            document,
            validation,
            "01-source-upper-assembly-isometric.png",
            "Current Lite3 Pro compact source upper assembly - isometric",
            25,
            -55,
        ),
        render(
            document,
            validation,
            "02-source-upper-assembly-side.png",
            "Current Lite3 Pro compact source upper assembly - 15 degree side view",
            0,
            -90,
            True,
        ),
    ]
    App.closeDocument(document.Name)
    print(
        json.dumps(
            {"outputs": [str(path.relative_to(PACKAGE_DIR)) for path in outputs]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
