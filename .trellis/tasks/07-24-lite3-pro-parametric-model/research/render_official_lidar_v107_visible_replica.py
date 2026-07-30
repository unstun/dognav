#!/usr/bin/env python3
"""Render the factory-visible V1.0.7 replica candidate in FreeCAD."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Mesh
from PySide import QtCore


TASK_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    TASK_ROOT / "evidence/official-lidar-v107-visible-replica-candidate"
)
MANIFEST = OUTPUT_ROOT / "manifest.json"
FCSTD_PATH = (
    OUTPUT_ROOT / "models/lite3_lidar_v107_visible_replica_candidate.FCStd"
)


def normalized_color(rgba: list[int]) -> tuple[float, float, float]:
    return tuple(float(channel) / 255.0 for channel in rgba[:3])


def add_mesh(document: App.Document, entry: dict[str, object]) -> object:
    name = str(entry["node_name"])
    obj = document.addObject("Mesh::Feature", name)
    obj.Label = name
    obj.addProperty("App::PropertyString", "EvidenceClass", "Evidence")
    obj.EvidenceClass = str(entry["evidence_class"])
    obj.Mesh = Mesh.Mesh(str(entry["path"]))
    obj.ViewObject.ShapeColor = normalized_color(entry["color_rgba"])
    obj.ViewObject.LineColor = (0.08, 0.09, 0.10)
    if name == "MID360_OPTICAL_WINDOW":
        obj.ViewObject.Transparency = 5
    if "Shaded" in obj.ViewObject.listDisplayModes():
        obj.ViewObject.DisplayMode = "Shaded"
    if "CreaseAngle" in obj.ViewObject.PropertiesList:
        obj.ViewObject.CreaseAngle = 38.0
    if "Lighting" in obj.ViewObject.PropertiesList:
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
    document = App.newDocument("Lite3_LiDAR_V107_Visible_Replica")
    try:
        objects = {
            str(entry["node_name"]): add_mesh(document, entry)
            for entry in manifest["entries"]
        }
        objects["LITE3_TOP_CONTACT_SURFACE"].ViewObject.Visibility = False
        document.recompute()
        document.saveAs(str(FCSTD_PATH))

        view = Gui.activeDocument().activeView()
        view.setAnimationEnabled(False)
        view.setAxisCross(False)
        view.setCameraType("Orthographic")

        for method, output_name in (
            ("viewAxonometric", "full-standing-isometric.png"),
            ("viewRight", "full-standing-front.png"),
            ("viewFront", "full-standing-side.png"),
            ("viewLeft", "full-standing-rear.png"),
            ("viewTop", "full-standing-top.png"),
        ):
            save_view(view, method, output_name, 0.88)

        objects["FULL_LITE3_OFFICIAL_VISUAL"].ViewObject.Visibility = False
        for method, output_name in (
            ("viewAxonometric", "upper-assembly-isometric.png"),
            ("viewRight", "upper-assembly-front.png"),
            ("viewFront", "upper-assembly-side.png"),
            ("viewLeft", "upper-assembly-rear.png"),
            ("viewTop", "upper-assembly-top.png"),
            ("viewBottom", "upper-assembly-bottom-visible-only.png"),
        ):
            save_view(view, method, output_name, 0.82)

        objects["FULL_LITE3_OFFICIAL_VISUAL"].ViewObject.Visibility = True
        document.save()
        print(f"model={FCSTD_PATH}", flush=True)
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
