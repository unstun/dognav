#!/usr/bin/env python3
"""Render the Lite3 Pro to J17A real-assembly candidate in FreeCAD."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Mesh
from PySide import QtCore
from pivy import coin


TASK_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = TASK_ROOT / "evidence/pro-j17a-real-assembly-candidate"
MANIFEST_PATH = OUTPUT_ROOT / "manifest.json"

SOURCE_COLORS = {
    "TORSO": (0.82, 0.84, 0.87),
    "FULL_LITE3_OFFICIAL_VISUAL": (0.82, 0.84, 0.87),
    "BZ20_BACKLOAD_SHELL_SOURCE": (0.92, 0.93, 0.94),
    "J17A_SENSOR_CARRIER_SOURCE": (0.38, 0.41, 0.45),
    "MID360_ADAPTER": (0.62, 0.64, 0.66),
    "MID360_GUARD": (0.08, 0.09, 0.11),
    "MID360_BODY": (0.76, 0.78, 0.80),
    "MID360_HOUSING_EXTERIOR": (0.82, 0.83, 0.84),
    "MID360_OPTICAL_WINDOW": (0.03, 0.27, 0.58),
    "MID360_CONNECTOR": (0.08, 0.09, 0.11),
    "D435I_CAMERA_DIRECT": (0.70, 0.72, 0.75),
    "D435_DIRECT_FASTENER_REFERENCES": (0.08, 0.09, 0.11),
}

ADAPTER_COLOR = (0.20, 0.31, 0.39)
FASTENER_COLOR = (0.08, 0.09, 0.10)
RECEIVER_COLOR = (0.10, 0.45, 0.78)

UPPER_STACK_NAMES = {
    "J17A_SENSOR_CARRIER_SOURCE",
    "MID360_ADAPTER",
    "MID360_GUARD",
    "MID360_BODY",
    "MID360_HOUSING_EXTERIOR",
    "MID360_OPTICAL_WINDOW",
    "MID360_CONNECTOR",
    "D435I_CAMERA_DIRECT",
    "D435_DIRECT_FASTENER_REFERENCES",
}


def source_full_body_path(manifest: dict[str, object]) -> Path:
    source_manifest = json.loads(
        Path(str(manifest["source_candidate_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    entry = next(
        item
        for item in source_manifest["entries"]
        if item["node_name"] == "FULL_LITE3_OFFICIAL_VISUAL"
    )
    return Path(str(entry["path"]))


def configure_object(obj: App.DocumentObject) -> None:
    name = obj.Name
    if name in SOURCE_COLORS:
        obj.ViewObject.ShapeColor = SOURCE_COLORS[name]
    elif name == "PRO_TO_J17A_OPEN_TRUSS_ADAPTER":
        obj.ViewObject.ShapeColor = ADAPTER_COLOR
    elif name.startswith("PRO_M3X8_SCREW_") or name.startswith(
        "J17A_M3X20_SCREW_"
    ):
        obj.ViewObject.ShapeColor = FASTENER_COLOR
    elif name.startswith("LITE3_PRO_M3_RECEIVER_PROXY_"):
        obj.ViewObject.ShapeColor = RECEIVER_COLOR
        obj.ViewObject.Transparency = 35
    if "LineColor" in obj.ViewObject.PropertiesList:
        obj.ViewObject.LineColor = (0.06, 0.07, 0.08)
    if "DisplayMode" in obj.ViewObject.PropertiesList:
        modes = obj.ViewObject.listDisplayModes()
        if "Shaded" in modes:
            obj.ViewObject.DisplayMode = "Shaded"
    if "CreaseAngle" in obj.ViewObject.PropertiesList:
        obj.ViewObject.CreaseAngle = 35.0
    if (
        name
        in {
            "TORSO",
            "FULL_LITE3_OFFICIAL_VISUAL",
            "D435I_CAMERA_DIRECT",
        }
        and "Lighting" in obj.ViewObject.PropertiesList
    ):
        obj.ViewObject.Lighting = "Two side"
    if name == "MID360_OPTICAL_WINDOW":
        obj.ViewObject.Transparency = 8


def save_view(
    view: object,
    method: str,
    output_name: str,
    fit_factor: float,
    width: int = 1800,
    height: int = 1350,
) -> None:
    getattr(view, method)()
    view.fitAll(fit_factor)
    Gui.updateGui()
    path = OUTPUT_ROOT / output_name
    view.saveImage(str(path), width, height, "White")
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"FreeCAD did not write {path}")
    print(f"render={path}", flush=True)


def set_visible(
    objects: dict[str, App.DocumentObject],
    names: set[str],
) -> None:
    for name, obj in objects.items():
        if obj.TypeId == "App::DocumentObjectGroup":
            obj.ViewObject.Visibility = True
        else:
            obj.ViewObject.Visibility = name in names


def shift_z(obj: App.DocumentObject, delta_mm: float) -> None:
    placement = obj.Placement
    placement.Base = App.Vector(
        placement.Base.x,
        placement.Base.y,
        placement.Base.z + delta_mm,
    )
    obj.Placement = placement


def render() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assembly_path = Path(
        str(manifest["editable_outputs"]["assembly_fcstd"])
    )
    document = App.openDocument(str(assembly_path))
    try:
        full_body = document.addObject(
            "Mesh::Feature",
            "FULL_LITE3_OFFICIAL_VISUAL",
        )
        full_body.Label = "Official full-standing Lite3 visual"
        full_body.Mesh = Mesh.Mesh(str(source_full_body_path(manifest)))

        objects = {
            obj.Name: obj
            for obj in document.Objects
            if hasattr(obj, "ViewObject")
        }
        for obj in objects.values():
            configure_object(obj)
        document.recompute()

        view = Gui.activeDocument().activeView()
        view.setAnimationEnabled(False)
        view.setAxisCross(False)
        view.setCameraType("Perspective")

        full_assembled = (
            {
                "FULL_LITE3_OFFICIAL_VISUAL",
                "BZ20_BACKLOAD_SHELL_SOURCE",
                "PRO_TO_J17A_OPEN_TRUSS_ADAPTER",
            }
            | UPPER_STACK_NAMES
            | {
                name
                for name in objects
                if name.startswith("PRO_M3X8_SCREW_")
                or name.startswith("J17A_M3X20_SCREW_")
            }
        )
        set_visible(objects, full_assembled)
        save_view(
            view,
            "viewAxonometric",
            "full-standing-assembled-isometric.png",
            0.88,
        )
        save_view(
            view,
            "viewFront",
            "full-standing-assembled-side.png",
            0.88,
        )
        save_view(
            view,
            "viewTop",
            "full-standing-assembled-top.png",
            0.88,
        )

        engineering = (
            {
                "TORSO",
                "BZ20_BACKLOAD_SHELL_SOURCE",
                "PRO_TO_J17A_OPEN_TRUSS_ADAPTER",
            }
            | UPPER_STACK_NAMES
            | {
                name
                for name in objects
                if name.startswith("PRO_M3X8_SCREW_")
                or name.startswith("J17A_M3X20_SCREW_")
                or name.startswith("LITE3_PRO_M3_RECEIVER_PROXY_")
            }
        )
        set_visible(objects, engineering)
        objects["TORSO"].ViewObject.Transparency = 70
        objects["BZ20_BACKLOAD_SHELL_SOURCE"].ViewObject.Transparency = 28
        save_view(
            view,
            "viewAxonometric",
            "engineering-assembled-isometric.png",
            0.80,
        )
        save_view(
            view,
            "viewTop",
            "engineering-assembled-top.png",
            0.80,
        )

        objects["TORSO"].ViewObject.Visibility = False
        objects["BZ20_BACKLOAD_SHELL_SOURCE"].ViewObject.Visibility = False
        save_view(
            view,
            "viewBottom",
            "engineering-underside.png",
            0.78,
        )

        original_placements = {
            name: obj.Placement
            for name, obj in objects.items()
            if name in UPPER_STACK_NAMES
            or name.startswith("PRO_M3X8_SCREW_")
            or name.startswith("J17A_M3X20_SCREW_")
            or name.startswith("LITE3_PRO_M3_RECEIVER_PROXY_")
        }
        for name in UPPER_STACK_NAMES:
            shift_z(objects[name], 35.0)
        for name, obj in objects.items():
            if name.startswith("J17A_M3X20_SCREW_"):
                shift_z(obj, 17.0)
            elif name.startswith("PRO_M3X8_SCREW_"):
                shift_z(obj, 14.0)
            elif name.startswith("LITE3_PRO_M3_RECEIVER_PROXY_"):
                shift_z(obj, -10.0)
        document.recompute()
        save_view(
            view,
            "viewAxonometric",
            "engineering-exploded-isometric.png",
            0.72,
        )
        for name, placement in original_placements.items():
            objects[name].Placement = placement
        document.recompute()

        objects["TORSO"].ViewObject.Visibility = True
        objects["TORSO"].ViewObject.Transparency = 45
        section_plane = coin.SoClipPlane()
        section_plane.plane.setValue(
            coin.SbPlane(
                coin.SbVec3f(0.0, -1.0, 0.0),
                0.0,
            )
        )
        scene_graph = view.getSceneGraph()
        scene_graph.insertChild(section_plane, 0)
        try:
            save_view(
                view,
                "viewAxonometric",
                "engineering-half-section.png",
                0.78,
            )
        finally:
            scene_graph.removeChild(section_plane)
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
