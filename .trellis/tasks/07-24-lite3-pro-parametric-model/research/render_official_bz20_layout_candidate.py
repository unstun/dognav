#!/usr/bin/env python3
"""Render the source-backed J17A/BZ20 layout candidate."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Mesh
from PySide import QtCore


TASK_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = TASK_ROOT / "evidence/official-bz20-layout-candidate"
MANIFEST = OUTPUT_ROOT / "manifest.json"

COLORS = {
    "TORSO": (0.82, 0.84, 0.87),
    "FULL_LITE3_OFFICIAL_VISUAL": (0.82, 0.84, 0.87),
    "BZ20_BACKLOAD_SHELL_SOURCE": (0.92, 0.93, 0.94),
    "J17A_SENSOR_CARRIER_SOURCE": (0.42, 0.44, 0.47),
    "MID360_ADAPTER": (0.58, 0.60, 0.62),
    "MID360_GUARD": (0.10, 0.11, 0.13),
    "MID360_BODY": (0.76, 0.78, 0.80),
    "MID360_HOUSING_EXTERIOR": (0.82, 0.83, 0.84),
    "MID360_OPTICAL_WINDOW": (0.04, 0.28, 0.58),
    "MID360_CONNECTOR": (0.10, 0.11, 0.13),
    "D435I_CAMERA_DIRECT": (0.72, 0.74, 0.77),
    "D435_DIRECT_FASTENER_REFERENCES": (0.10, 0.11, 0.13),
    "J17A_FOUR_MOUNT_FASTENER_REFERENCES": (0.10, 0.11, 0.13),
}


def add_mesh(document: App.Document, entry: dict[str, object]) -> object:
    name = str(entry["node_name"])
    obj = document.addObject("Mesh::Feature", name)
    obj.Label = name
    obj.Mesh = Mesh.Mesh(str(entry["path"]))
    obj.ViewObject.ShapeColor = COLORS[name]
    obj.ViewObject.LineColor = (0.08, 0.09, 0.10)
    if name == "MID360_OPTICAL_WINDOW":
        obj.ViewObject.Transparency = 8
    if "Shaded" in obj.ViewObject.listDisplayModes():
        obj.ViewObject.DisplayMode = "Shaded"
    if "CreaseAngle" in obj.ViewObject.PropertiesList:
        obj.ViewObject.CreaseAngle = 40.0
    if (
        name in {"FULL_LITE3_OFFICIAL_VISUAL", "D435I_CAMERA_DIRECT"}
        and "Lighting" in obj.ViewObject.PropertiesList
    ):
        obj.ViewObject.Lighting = "Two side"
    return obj


def save_view(
    view: object,
    method: str,
    output_name: str,
    fit_factor: float,
) -> None:
    getattr(view, method)()
    view.fitAll(fit_factor)
    Gui.updateGui()
    path = OUTPUT_ROOT / output_name
    view.saveImage(str(path), 1800, 1350, "White")
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"FreeCAD did not write {path}")
    print(f"render={path}", flush=True)


def render() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    document = App.newDocument("Official_BZ20_Layout_Candidate")
    try:
        objects = {
            str(entry["node_name"]): add_mesh(document, entry)
            for entry in manifest["entries"]
        }
        objects["TORSO"].ViewObject.Visibility = False
        objects[
            "J17A_FOUR_MOUNT_FASTENER_REFERENCES"
        ].ViewObject.Visibility = False
        document.recompute()
        view = Gui.activeDocument().activeView()
        view.setAnimationEnabled(False)
        view.setAxisCross(False)
        view.setCameraType("Perspective")

        save_view(
            view,
            "viewAxonometric",
            "full-standing-isometric.png",
            0.88,
        )
        save_view(view, "viewTop", "full-standing-top.png", 0.88)
        save_view(view, "viewRight", "full-standing-front.png", 0.88)
        save_view(view, "viewFront", "full-standing-side.png", 0.88)

        objects["FULL_LITE3_OFFICIAL_VISUAL"].ViewObject.Visibility = False
        save_view(
            view,
            "viewAxonometric",
            "source-parts-isometric.png",
            0.82,
        )
        objects[
            "J17A_FOUR_MOUNT_FASTENER_REFERENCES"
        ].ViewObject.Visibility = True
        save_view(
            view,
            "viewBottom",
            "mounting-relationships-bottom.png",
            0.82,
        )
    finally:
        App.closeDocument(document.Name)


def render_and_quit() -> None:
    exit_code = 0
    try:
        render()
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        QtCore.QCoreApplication.exit(exit_code)


QtCore.QTimer.singleShot(500, render_and_quit)
