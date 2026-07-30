"""Render the compact current-Pro sensor layout and old-carrier comparison."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


PACKAGE_DIR = Path(__file__).resolve().parent
RENDER_DIR = PACKAGE_DIR / "renders"


def render_top() -> Path:
    fig, ax = plt.subplots(figsize=(14, 9), dpi=150)
    ax.add_patch(Rectangle((-305, -54), 209, 108, fc="#d84a42", ec="#c93b34", alpha=0.10, lw=2, ls="--"))
    ax.add_patch(Rectangle((-300, -50), 200, 100, fc="#d7dce2", ec="#697480", alpha=0.72, lw=2))
    ax.add_patch(Rectangle((-92, -57.5), 110, 115, fill=False, ec="#7041b6", lw=3, label="compact 110 x 115 planning surface"))
    ax.add_patch(Rectangle((-90, -52.5), 105, 105, fc="#c8a978", ec="#8b6b3e", alpha=0.48, lw=2, label="S410 raw B-rep plan bound"))
    ax.add_patch(Rectangle((-70.9, -36.4), 66.8, 72.7, fc="#334fa3", ec="#1e347d", alpha=0.55, lw=2, label="Mid-360 official B-rep plan bound"))
    ax.add_patch(Rectangle((-7.5, -45), 25, 90, fc="#92a7bc", ec="#50687d", alpha=0.72, lw=2, label="D435i official 90 x 25 plan envelope"))
    for x, y in [(0,32.5),(0,-32.5)]:
        ax.add_patch(Circle((x,y),3.5,fc="#1769d1",ec="white",lw=1.5,zorder=8))
    ax.add_patch(Circle((-75,0),3.8,fc="#f4a40b",ec="white",lw=1.5,zorder=8))
    ax.axvline(20,color="#2b9a50",lw=2,label="measured nose edge")
    ax.axvline(-96,color="#d64b43",lw=1.5,ls="--")
    ax.annotate("6 mm",xy=(-90,60),xytext=(-96,60),arrowprops=dict(arrowstyle="<->",color="#b2342e",lw=2),ha="center",va="bottom",color="#b2342e",fontsize=11)
    ax.annotate("2.5 mm",xy=(17.5,-62),xytext=(20,-62),arrowprops=dict(arrowstyle="<->",color="#278b49",lw=2),ha="center",va="top",color="#278b49",fontsize=11)
    ax.text(-37.5,0,"S410 + Mid-360\ncompact source geometry",ha="center",va="center",fontsize=12,color="#4a3823")
    ax.text(5,0,"D435i",ha="center",va="center",fontsize=11,color="#334c61",rotation=90)
    ax.set_title("Current Lite3 Pro compact sensor layout Rev A - source geometry layout, no carrier solid",fontsize=16,pad=16)
    ax.set_xlabel("x: robot forward (mm)"); ax.set_ylabel("y: robot left (mm)")
    ax.set_aspect("equal",adjustable="box"); ax.set_xlim(-320,45); ax.set_ylim(-90,90)
    ax.grid(True,color="#e2e6ea",lw=.7); ax.legend(loc="lower left",framealpha=.96)
    fig.tight_layout(); out=RENDER_DIR/"01-compact-source-layout-top.png"; fig.savefig(out,bbox_inches="tight",facecolor="white"); plt.close(fig); return out


def render_comparison() -> Path:
    fig, (top,bottom)=plt.subplots(2,1,figsize=(14,7),dpi=150,sharex=True)
    for ax in (top,bottom):
        ax.axvspan(-305,-96,color="#d84a42",alpha=.12)
        ax.axvline(-96,color="#d64b43",ls="--",lw=2)
        ax.axvline(20,color="#2b9a50",lw=2)
        ax.set_ylim(0,1); ax.set_yticks([]); ax.grid(True,axis="x",color="#e2e6ea")
    top.add_patch(Rectangle((-96,0.25),153.734544,.5,fc="#c2a277",ec="#7c5d32",lw=2))
    top.text(-19.1,.5,"retained V1 carrier envelope 153.7 mm",ha="center",va="center",fontsize=12)
    top.annotate("37.7 mm longer than the measured front zone",xy=(57.7,.82),xytext=(20,.82),arrowprops=dict(arrowstyle="<->",color="#b2342e",lw=2),ha="center",color="#b2342e")
    top.set_title("Rejected old carrier length: cannot remain wholly inside the current front zone",fontsize=14)
    bottom.add_patch(Rectangle((-92,.25),110,.5,fc="#a78bd4",ec="#7041b6",lw=2))
    bottom.text(-37,.5,"compact planning envelope 110 mm",ha="center",va="center",fontsize=12)
    bottom.annotate("6 mm",xy=(-92,.82),xytext=(-96,.82),arrowprops=dict(arrowstyle="<->",color="#b2342e",lw=2),ha="center",color="#b2342e")
    bottom.annotate("2 mm",xy=(18,.82),xytext=(20,.82),arrowprops=dict(arrowstyle="<->",color="#278b49",lw=2),ha="center",color="#278b49")
    bottom.set_title("Compact current-Pro layout: fits in plan, but receiver and structure are still open",fontsize=14)
    bottom.set_xlabel("x: robot forward (mm); red region is the uncertainty-expanded compute-box keep-out")
    bottom.set_xlim(-320,70)
    fig.tight_layout(); out=RENDER_DIR/"02-old-versus-compact-length-comparison.png"; fig.savefig(out,bbox_inches="tight",facecolor="white"); plt.close(fig); return out


def main() -> None:
    RENDER_DIR.mkdir(parents=True,exist_ok=True)
    outputs=[render_top(),render_comparison()]
    print(json.dumps({"outputs":[str(p.relative_to(PACKAGE_DIR)) for p in outputs]},indent=2))


if __name__ == "__main__":
    main()
