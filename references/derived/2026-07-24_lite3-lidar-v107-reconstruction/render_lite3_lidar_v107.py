#!/usr/bin/env python3
"""Render repeatable evidence views of the Lite3 LiDAR V1.0.7 model."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore


ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "models" / "lite3_lidar_v107_reconstruction.FCStd"
EVIDENCE = ROOT / "evidence"
PARAMETERS = ROOT / "model_parameters.json"

def configure_document() -> tuple[App.Document, object]:
    if not MODEL.exists():
        raise FileNotFoundError(MODEL)
    if not PARAMETERS.exists():
        raise FileNotFoundError(PARAMETERS)
    with PARAMETERS.open("r", encoding="utf-8") as handle:
        parameters = json.load(handle)
    if parameters.get("model_id") != "lite3_lidar_v107_visual_reconstruction":
        raise ValueError("Unexpected model_parameters.json model_id")
    colors = parameters.get("visual", {}).get("colors_rgb", {})
    if not colors:
        raise ValueError("Missing visual.colors_rgb")

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    document = App.openDocument(str(MODEL))
    Gui.activeDocument().activeView().setAnimationEnabled(False)
    Gui.activeDocument().activeView().setAxisCross(False)
    Gui.activeDocument().activeView().setCameraType("Perspective")

    for name, color in colors.items():
        object_ = document.getObject(name)
        if object_ is None:
            raise ValueError(f"Missing render object: {name}")
        object_.ViewObject.Visibility = True
        object_.ViewObject.ShapeColor = tuple(color)
        object_.ViewObject.LineColor = (0.12, 0.12, 0.12)
        if "Shaded" in object_.ViewObject.listDisplayModes():
            object_.ViewObject.DisplayMode = "Shaded"

    document.recompute()
    return document, Gui.activeDocument().activeView()


def save_view(view: object, method_name: str, output_name: str) -> None:
    getattr(view, method_name)()
    view.fitAll(0.86)
    Gui.updateGui()
    output = EVIDENCE / output_name
    view.saveImage(str(output), 1800, 1350, "White")
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError(f"FreeCAD did not write {output}")
    print(f"render={output}", flush=True)


def render_and_quit() -> None:
    exit_code = 0
    document = None
    try:
        document, view = configure_document()
        save_view(view, "viewFront", "freecad-front.png")
        save_view(view, "viewRear", "freecad-rear.png")
        save_view(view, "viewLeft", "freecad-left.png")
        save_view(view, "viewRight", "freecad-right.png")
        save_view(view, "viewTop", "freecad-top.png")
        save_view(view, "viewAxonometric", "freecad-isometric.png")

        base = document.getObject("Official_Lite3_Base_Mesh")
        base.ViewObject.Visibility = False
        front_sensor_bar = document.getObject("Front_Sensor_Bar")
        front_sensor_bar.ViewObject.Visibility = False
        document.recompute()
        save_view(view, "viewAxonometric", "upper-module-isometric.png")
        save_view(view, "viewTop", "upper-module-top.png")
        save_view(view, "viewBottom", "upper-module-bottom.png")
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        if document is not None:
            App.closeDocument(document.Name)
        QtCore.QCoreApplication.exit(exit_code)


QtCore.QTimer.singleShot(500, render_and_quit)
