#!/usr/bin/env python3
"""Render the Pro/Interface minimum-forward-shift placement candidate."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Mesh
from PySide import QtCore


TASK_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = TASK_ROOT / "evidence/pro-clearance-placement-candidate"
MANIFEST = OUTPUT_ROOT / "manifest.json"

COLORS = {
    "TORSO": (0.82, 0.84, 0.87),
    "FACTORY_INTERFACE": (0.76, 0.78, 0.80),
    "FACTORY_INTERFACE_CONNECTORS": (0.10, 0.11, 0.13),
    "FACTORY_INTERFACE_VENTS": (0.18, 0.19, 0.21),
    "J17A_ORIGINAL_POSITION_GHOST": (0.88, 0.08, 0.05),
    "J17A_SENSOR_CARRIER_SOURCE": (0.42, 0.44, 0.47),
    "MID360_ADAPTER": (0.58, 0.60, 0.62),
    "MID360_GUARD": (0.10, 0.11, 0.13),
    "MID360_BODY": (0.76, 0.78, 0.80),
    "MID360_HOUSING_EXTERIOR": (0.82, 0.83, 0.84),
    "MID360_OPTICAL_WINDOW": (0.04, 0.28, 0.58),
    "MID360_CONNECTOR": (0.10, 0.11, 0.13),
    "D435I_CAMERA_DIRECT": (0.72, 0.74, 0.77),
    "D435_DIRECT_FASTENER_REFERENCES": (0.12, 0.13, 0.15),
    "J17A_FOUR_FASTENER_REFERENCES": (0.12, 0.13, 0.15),
    "LITE3_PRO_74X94_HOLE_AXIS_REFERENCES": (0.04, 0.45, 0.78),
}


def add_mesh(document: App.Document, entry: dict[str, object]) -> object:
    name = str(entry["node_name"])
    obj = document.addObject("Mesh::Feature", name)
    obj.Label = name
    obj.Mesh = Mesh.Mesh(str(entry["path"]))
    obj.ViewObject.ShapeColor = COLORS[name]
    obj.ViewObject.LineColor = (0.08, 0.09, 0.10)
    if name == "J17A_ORIGINAL_POSITION_GHOST":
        obj.ViewObject.Transparency = 76
    if name == "MID360_OPTICAL_WINDOW":
        obj.ViewObject.Transparency = 8
    if name == "LITE3_PRO_74X94_HOLE_AXIS_REFERENCES":
        obj.ViewObject.Transparency = 15
    if "Shaded" in obj.ViewObject.listDisplayModes():
        obj.ViewObject.DisplayMode = "Shaded"
    if "CreaseAngle" in obj.ViewObject.PropertiesList:
        obj.ViewObject.CreaseAngle = 45.0
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
    document = App.newDocument("Pro_Clearance_Placement_Candidate")
    try:
        objects = {
            str(entry["node_name"]): add_mesh(document, entry)
            for entry in manifest["entries"]
        }
        document.recompute()
        view = Gui.activeDocument().activeView()
        view.setAnimationEnabled(False)
        view.setAxisCross(False)
        view.setCameraType("Perspective")

        objects[
            "LITE3_PRO_74X94_HOLE_AXIS_REFERENCES"
        ].ViewObject.Visibility = False
        objects[
            "J17A_ORIGINAL_POSITION_GHOST"
        ].ViewObject.Visibility = False
        save_view(
            view,
            "viewAxonometric",
            "shifted-body-context-isometric.png",
            0.88,
        )
        save_view(
            view,
            "viewTop",
            "shifted-body-context-top.png",
            0.88,
        )
        save_view(
            view,
            "viewRight",
            "shifted-body-context-front.png",
            0.88,
        )

        objects[
            "J17A_ORIGINAL_POSITION_GHOST"
        ].ViewObject.Visibility = True
        save_view(
            view,
            "viewTop",
            "shift-diagnostic-top.png",
            0.88,
        )
        save_view(
            view,
            "viewAxonometric",
            "shift-diagnostic-isometric.png",
            0.88,
        )

        objects[
            "LITE3_PRO_74X94_HOLE_AXIS_REFERENCES"
        ].ViewObject.Visibility = True
        save_view(
            view,
            "viewBottom",
            "mounting-axes-diagnostic-bottom.png",
            0.88,
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
