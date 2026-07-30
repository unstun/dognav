"""Render the scan-registered planar interface and keep-out revision."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle


ROOT = Path(__file__).resolve().parent
PARAMETERS = json.loads((ROOT / "parameters.json").read_text())


def main() -> None:
    bounds = PARAMETERS["compute_enclosure"]["scan_registered_nominal_bounds_mm"]
    expanded = PARAMETERS["compute_enclosure"]["expanded_collision_keepout_bounds_mm"]
    deck = [(20, -45), (20, 45), (5, 58), (-100, 70), (-100, -70), (5, -58)]
    fig, ax = plt.subplots(figsize=(14, 8), dpi=160)
    ax.add_patch(Polygon(deck, closed=True, fc="#eef1f4", ec="#56616d", lw=2, label="planar deck proxy"))
    footprint = PARAMETERS["compute_enclosure"]["scan_registered_nominal_footprint_polygon_mm"]
    ax.add_patch(Polygon(footprint, closed=True, fc="#d8dde3", ec="#596571", lw=2, label="scan-registered notched enclosure top"))
    ax.add_patch(Rectangle((expanded["x"][0], expanded["y"][0]), expanded["x"][1] - expanded["x"][0], expanded["y"][1] - expanded["y"][0], fill=False, ec="#d34c43", lw=2.5, ls="--", label="revised expanded keep-out"))
    # Previous photo-only keepout makes the lateral correction visible.
    ax.add_patch(Rectangle((-305, -54), 209, 108, fill=False, ec="#888f98", lw=1.5, ls=":", label="previous photo-only keep-out"))
    for y in (32.5, -32.5):
        ax.add_patch(Circle((0, y), 4, fc="#1769d1", ec="white", lw=1.5, zorder=5))
    ax.add_patch(Circle((-75, 0), 4, fc="#f4a40b", ec="white", lw=1.5, zorder=5))
    ax.axvline(20, color="#169f90", lw=2, ls="--", label="usable nose edge")
    ax.text(-199.8, 0, "scan top\n199.6 x 108.6 mm\n2 front recesses", ha="center", va="center", fontsize=12, color="#35404b")
    ax.annotate("left recess\n~30 x 11.9 mm", xy=(-130, 44), xytext=(-92, 72), arrowprops=dict(arrowstyle="->", color="#596571"), fontsize=10, color="#35404b")
    ax.annotate("right recess\n~30 x 10.7 mm", xy=(-130, -42), xytext=(-92, -83), arrowprops=dict(arrowstyle="->", color="#596571"), fontsize=10, color="#35404b")
    ax.text(4, 39, "65 mm pair\nthread/depth open", fontsize=10, color="#10539f")
    ax.set_title("Current Lite3 Professional — scan-registered planar interface Rev B\nreference only; no printable adapter", fontsize=15)
    ax.set_xlabel("X forward (mm)")
    ax.set_ylabel("Y left (mm)")
    ax.set_xlim(-320, 45)
    ax.set_ylim(-95, 95)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color="#e1e5e9", lw=0.7)
    ax.legend(loc="lower left", framealpha=0.97)
    output = ROOT / "renders" / "01-scan-registered-interface-top.png"
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
