#!/usr/bin/env python3
"""Render the official FAST-LIVO2 BZ20 and AGX-base source meshes."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Mesh
from PySide import QtCore


TASK_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = TASK_ROOT / "evidence/official-fast-livo2-compute-parts"
MANIFEST = OUTPUT_ROOT / "manifest.json"

COLORS = {
    "BZ20_BACKLOAD_SHELL_SOURCE": (0.82, 0.84, 0.87),
    "AGX_ORIN_BASE_SOURCE": (0.18, 0.19, 0.21),
}


def save_view(
    view: object,
    method: str,
    output_name: str,
    fit_factor: float = 0.80,
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
    document = App.newDocument("Official_FAST_LIVO2_Compute_Parts")
    try:
        objects = {}
        for name, entry in manifest["parts"].items():
            obj = document.addObject("Mesh::Feature", name)
            obj.Label = name
            obj.Mesh = Mesh.Mesh(str(entry["mesh_path"]))
            obj.ViewObject.ShapeColor = COLORS[name]
            obj.ViewObject.LineColor = (0.08, 0.09, 0.10)
            if "Shaded" in obj.ViewObject.listDisplayModes():
                obj.ViewObject.DisplayMode = "Shaded"
            if "CreaseAngle" in obj.ViewObject.PropertiesList:
                obj.ViewObject.CreaseAngle = 35.0
            objects[name] = obj

        document.recompute()
        view = Gui.activeDocument().activeView()
        view.setAnimationEnabled(False)
        view.setAxisCross(False)
        view.setCameraType("Perspective")

        for name, obj in objects.items():
            for other in objects.values():
                other.ViewObject.Visibility = other is obj
            stem = name.lower()
            save_view(view, "viewAxonometric", f"{stem}-isometric.png")
            save_view(view, "viewTop", f"{stem}-top.png")
            save_view(view, "viewFront", f"{stem}-front.png")
            save_view(view, "viewRight", f"{stem}-right.png")
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
