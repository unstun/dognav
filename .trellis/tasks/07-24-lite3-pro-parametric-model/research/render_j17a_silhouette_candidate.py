#!/usr/bin/env python3
"""Render the evidence-only J17A silhouette candidate in FreeCAD."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Mesh
from PySide import QtCore


TASK_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = TASK_ROOT / "evidence/j17a-silhouette-candidate"
MANIFEST = OUTPUT_ROOT / "manifest.json"

COLORS = {
    "TORSO": (0.80, 0.82, 0.85),
    "FACTORY_INTERFACE": (0.76, 0.78, 0.80),
    "FACTORY_INTERFACE_CONNECTORS": (0.10, 0.11, 0.13),
    "FACTORY_INTERFACE_VENTS": (0.18, 0.19, 0.21),
    "MID360_ADAPTER": (0.58, 0.60, 0.62),
    "MID360_GUARD": (0.10, 0.11, 0.13),
    "MID360_BODY": (0.76, 0.78, 0.80),
    "MID360_HOUSING_EXTERIOR": (0.82, 0.83, 0.84),
    "MID360_OPTICAL_WINDOW": (0.04, 0.28, 0.58),
    "MID360_CONNECTOR": (0.10, 0.11, 0.13),
    "D435I_CAMERA": (0.72, 0.74, 0.77),
    "J17A_SENSOR_CARRIER_CANDIDATE": (0.92, 0.42, 0.08),
}


def add_mesh(document: App.Document, entry: dict[str, object]) -> object:
    path = Path(str(entry["path"]))
    name = str(entry["node_name"])
    obj = document.addObject("Mesh::Feature", name)
    obj.Label = name
    obj.Mesh = Mesh.Mesh(str(path))
    obj.ViewObject.ShapeColor = COLORS[name]
    obj.ViewObject.LineColor = (0.08, 0.09, 0.10)
    if name == "J17A_SENSOR_CARRIER_CANDIDATE":
        obj.ViewObject.Transparency = 12
    if name == "MID360_OPTICAL_WINDOW":
        obj.ViewObject.Transparency = 8
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
    with MANIFEST.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    document = App.newDocument("J17A_Silhouette_Candidate")
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

        objects["TORSO"].ViewObject.Visibility = False
        save_view(view, "viewAxonometric", "sensor-candidate-isometric.png", 0.82)
        save_view(view, "viewFront", "sensor-candidate-front.png", 0.84)
        save_view(view, "viewLeft", "sensor-candidate-left.png", 0.84)
        save_view(view, "viewRight", "sensor-candidate-right.png", 0.84)
        save_view(view, "viewTop", "sensor-candidate-top.png", 0.84)

        objects["TORSO"].ViewObject.Visibility = True
        save_view(
            view,
            "viewAxonometric",
            "body-context-candidate-isometric.png",
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
