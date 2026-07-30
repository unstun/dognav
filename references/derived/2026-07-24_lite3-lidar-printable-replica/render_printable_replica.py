#!/usr/bin/env python3
"""Render repeatable dual-track Lite3 reference and print views."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Mesh
from PySide import QtCore


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"
RENDER_MANIFEST = EVIDENCE / "render_cache" / "manifest.json"
COLORS = {
    "TORSO": (0.78, 0.80, 0.83),
    "HIP": (0.92, 0.93, 0.94),
    "THIGH": (0.82, 0.84, 0.87),
    "SHANK": (0.29, 0.32, 0.36),
    "UPPER_LIDAR_MODULE": (0.43, 0.46, 0.50),
    "UPPER_DECK_INTERFACE": (0.67, 0.69, 0.71),
    "MID360_SENSOR": (0.72, 0.74, 0.77),
    "MID360_OPTICAL_WINDOW": (0.04, 0.28, 0.58),
    "MID360_BODY": (0.76, 0.78, 0.80),
    "MID360_HOUSING_EXTERIOR": (0.82, 0.83, 0.84),
    "MID360_CONNECTOR": (0.10, 0.11, 0.13),
    "J17A_SENSOR_CARRIER": (0.42, 0.45, 0.48),
    "FACTORY_LIDAR_MOUNTS": (0.51, 0.53, 0.56),
    "MID360_ADAPTER": (0.58, 0.60, 0.62),
    "MID360_GUARD": (0.12, 0.13, 0.15),
    "FACTORY_INTERFACE": (0.36, 0.38, 0.40),
    "FACTORY_INTERFACE_CONNECTORS": (0.08, 0.09, 0.10),
    "FACTORY_INTERFACE_VENTS": (0.12, 0.13, 0.14),
    "FRONT_CAMERA_BAR": (0.72, 0.74, 0.77),
    "D435I_CAMERA": (0.72, 0.74, 0.77),
    "CAMERA_MOUNT_BRACKET": (0.27, 0.30, 0.34),
    "CAMERA_CARRIER_PLATE": (0.42, 0.45, 0.49),
    # Orange marks the non-factory receiver adaptation so its load path into
    # the black official-source S410 guard remains visually inspectable.
    "CAMERA_RECEIVER_YOKE": (0.86, 0.38, 0.10),
    "CAMERA_FASTENERS": (0.13, 0.15, 0.18),
}


def family(label: str) -> str:
    upper = label.upper()
    for exact in (
        "UPPER_DECK_INTERFACE",
        "UPPER_LIDAR_MODULE",
        "MID360_SENSOR",
        "MID360_OPTICAL_WINDOW",
        "MID360_BODY",
        "MID360_HOUSING_EXTERIOR",
        "MID360_CONNECTOR",
        "J17A_SENSOR_CARRIER",
        "FACTORY_LIDAR_MOUNTS",
        "MID360_ADAPTER",
        "MID360_GUARD",
        "FACTORY_INTERFACE_CONNECTORS",
        "FACTORY_INTERFACE_VENTS",
        "FACTORY_INTERFACE",
        "D435I_CAMERA",
        "CAMERA_MOUNT_BRACKET",
        "CAMERA_CARRIER_PLATE",
        "CAMERA_RECEIVER_YOKE",
        "CAMERA_FASTENERS",
        "FRONT_CAMERA_BAR",
    ):
        if exact in upper:
            return exact
    if "TORSO" in upper:
        return "TORSO"
    for candidate in ("SHANK", "THIGH", "HIP"):
        if candidate in upper:
            return candidate
    return "TORSO"


def add_mesh(
    document: App.Document,
    path: Path,
    name: str,
) -> object:
    if not path.is_file():
        raise FileNotFoundError(path)
    object_ = document.addObject("Mesh::Feature", name)
    object_.Label = name
    object_.Mesh = Mesh.Mesh(str(path))
    object_.ViewObject.ShapeColor = COLORS[family(name)]
    object_.ViewObject.LineColor = (0.10, 0.11, 0.13)
    if family(name) == "MID360_OPTICAL_WINDOW":
        object_.ViewObject.Transparency = 8
        if "ShapeMaterial" in object_.ViewObject.PropertiesList:
            object_.ViewObject.ShapeMaterial.Shininess = 75.0
    if "Shaded" in object_.ViewObject.listDisplayModes():
        object_.ViewObject.DisplayMode = "Shaded"
    if "CreaseAngle" in object_.ViewObject.PropertiesList:
        object_.ViewObject.CreaseAngle = 45.0
    if "Lighting" in object_.ViewObject.PropertiesList:
        object_.ViewObject.Lighting = "Two side"
    return object_


def configure_view() -> object:
    view = Gui.activeDocument().activeView()
    view.setAnimationEnabled(False)
    view.setAxisCross(False)
    view.setCameraType("Perspective")
    return view


def save_view(
    view: object,
    method_name: str,
    output_name: str,
    fit_factor: float = 0.88,
) -> None:
    getattr(view, method_name)()
    view.fitAll(fit_factor)
    Gui.updateGui()
    output = EVIDENCE / output_name
    view.saveImage(str(output), 1800, 1350, "White")
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"FreeCAD did not write {output}")
    print(f"render={output}", flush=True)


def add_manifest_meshes(
    document: App.Document,
    entries: list[dict[str, object]],
) -> list[object]:
    objects = []
    for entry in entries:
        object_ = add_mesh(
            document,
            Path(str(entry["path"])),
            str(entry["node_name"]),
        )
        objects.append(object_)
    return objects


def render_visual_reference(manifest: dict[str, object]) -> None:
    if not RENDER_MANIFEST.is_file():
        raise FileNotFoundError(RENDER_MANIFEST)
    document = App.newDocument("Lite3_Official_Visual_Reference")
    try:
        objects = add_manifest_meshes(document, manifest["visual_reference"])
        document.recompute()
        view = configure_view()
        save_view(
            view,
            "viewAxonometric",
            "visual-reference-isometric.png",
            0.84,
        )
        save_view(view, "viewFront", "visual-reference-front.png", 0.90)
        save_view(view, "viewRear", "visual-reference-rear.png", 0.90)
        save_view(view, "viewLeft", "visual-reference-left.png", 0.90)
        save_view(view, "viewRight", "visual-reference-right.png", 0.90)
        save_view(view, "viewTop", "visual-reference-top.png", 0.90)

        upper_families = {
            "UPPER_DECK_INTERFACE",
            "UPPER_LIDAR_MODULE",
            "MID360_SENSOR",
            "MID360_OPTICAL_WINDOW",
            "MID360_BODY",
            "MID360_HOUSING_EXTERIOR",
            "MID360_CONNECTOR",
            "FACTORY_LIDAR_MOUNTS",
            "MID360_ADAPTER",
            "MID360_GUARD",
            "FACTORY_INTERFACE",
            "FACTORY_INTERFACE_CONNECTORS",
            "FACTORY_INTERFACE_VENTS",
            "FRONT_CAMERA_BAR",
            "D435I_CAMERA",
            "CAMERA_MOUNT_BRACKET",
            "CAMERA_CARRIER_PLATE",
            "CAMERA_RECEIVER_YOKE",
            "CAMERA_FASTENERS",
        }
        for object_ in objects:
            object_.ViewObject.Visibility = family(object_.Label) in upper_families
        document.recompute()
        save_view(
            view,
            "viewAxonometric",
            "visual-reference-upper-isometric.png",
            0.80,
        )
        save_view(view, "viewTop", "visual-reference-upper-top.png", 0.84)
        save_view(
            view,
            "viewFront",
            "visual-reference-upper-front.png",
            0.84,
        )

        sensor_families = {
            "MID360_SENSOR",
            "MID360_OPTICAL_WINDOW",
            "MID360_BODY",
            "MID360_HOUSING_EXTERIOR",
            "MID360_CONNECTOR",
            "FACTORY_LIDAR_MOUNTS",
            "MID360_ADAPTER",
            "MID360_GUARD",
            "FACTORY_INTERFACE",
            "FACTORY_INTERFACE_CONNECTORS",
            "FACTORY_INTERFACE_VENTS",
            "FRONT_CAMERA_BAR",
            "D435I_CAMERA",
            "CAMERA_MOUNT_BRACKET",
            "CAMERA_CARRIER_PLATE",
            "CAMERA_RECEIVER_YOKE",
            "CAMERA_FASTENERS",
        }
        for object_ in objects:
            object_.ViewObject.Visibility = family(object_.Label) in sensor_families
        document.recompute()
        save_view(
            view,
            "viewAxonometric",
            "visual-reference-mid360-isometric.png",
            0.76,
        )
        save_view(
            view,
            "viewFront",
            "visual-reference-mid360-side.png",
            0.78,
        )
    finally:
        App.closeDocument(document.Name)


def render_printable_assembly(manifest: dict[str, object]) -> None:
    document = App.newDocument("Lite3_Printable_Assembly")
    try:
        objects = add_manifest_meshes(
            document,
            manifest["printable_assembled"],
        )
        document.recompute()
        view = configure_view()
        save_view(
            view,
            "viewAxonometric",
            "printable-assembly-isometric.png",
            0.84,
        )
        save_view(
            view,
            "viewLeft",
            "printable-assembly-left.png",
            0.90,
        )
        upper_families = {
            "UPPER_DECK_INTERFACE",
            "UPPER_LIDAR_MODULE",
            "MID360_SENSOR",
            "MID360_OPTICAL_WINDOW",
            "MID360_BODY",
            "MID360_HOUSING_EXTERIOR",
            "MID360_CONNECTOR",
            "FACTORY_LIDAR_MOUNTS",
            "MID360_ADAPTER",
            "MID360_GUARD",
            "FACTORY_INTERFACE",
            "FACTORY_INTERFACE_CONNECTORS",
            "FACTORY_INTERFACE_VENTS",
            "FRONT_CAMERA_BAR",
            "D435I_CAMERA",
            "CAMERA_MOUNT_BRACKET",
            "CAMERA_CARRIER_PLATE",
            "CAMERA_RECEIVER_YOKE",
            "CAMERA_FASTENERS",
        }
        for object_ in objects:
            object_.ViewObject.Visibility = (
                family(object_.Label) in upper_families
            )
        document.recompute()
        save_view(
            view,
            "viewAxonometric",
            "printable-assembly-upper-isometric.png",
            0.80,
        )
    finally:
        App.closeDocument(document.Name)


def render_d435i_diagnostic(manifest: dict[str, object]) -> None:
    visual_entries = [
        entry
        for entry in manifest["visual_reference"]
        if family(str(entry["node_name"]))
        in {
            "D435I_CAMERA",
            "CAMERA_MOUNT_BRACKET",
            "CAMERA_CARRIER_PLATE",
            "CAMERA_RECEIVER_YOKE",
            "CAMERA_FASTENERS",
        }
    ]
    if {family(str(entry["node_name"])) for entry in visual_entries} != {
        "D435I_CAMERA",
        "CAMERA_MOUNT_BRACKET",
        "CAMERA_CARRIER_PLATE",
        "CAMERA_RECEIVER_YOKE",
        "CAMERA_FASTENERS",
    }:
        raise ValueError("D435i visual/bracket/fastener nodes are incomplete")
    document = App.newDocument("D435i_Official_Visual_Diagnostic")
    try:
        add_manifest_meshes(document, visual_entries)
        document.recompute()
        view = configure_view()
        save_view(
            view,
            "viewAxonometric",
            "d435i-official-visual-isometric.png",
            0.76,
        )
        save_view(
            view,
            "viewRight",
            "d435i-official-visual-front.png",
            0.80,
        )
        save_view(
            view,
            "viewFront",
            "d435i-official-visual-side.png",
            0.80,
        )
        for object_ in document.Objects:
            object_.ViewObject.Visibility = (
                family(object_.Label) != "D435I_CAMERA"
            )
        document.recompute()
        save_view(
            view,
            "viewAxonometric",
            "d435i-bracket-fasteners-isometric.png",
            0.76,
        )
        save_view(
            view,
            "viewRight",
            "d435i-bracket-fasteners-end.png",
            0.80,
        )
        save_view(
            view,
            "viewTop",
            "d435i-bracket-fasteners-top.png",
            0.80,
        )
    finally:
        App.closeDocument(document.Name)

    receiver_entries = [
        entry
        for entry in manifest["visual_reference"]
        if family(str(entry["node_name"]))
        in {
            "MID360_GUARD",
            "D435I_CAMERA",
            "CAMERA_MOUNT_BRACKET",
            "CAMERA_CARRIER_PLATE",
            "CAMERA_RECEIVER_YOKE",
            "CAMERA_FASTENERS",
        }
    ]
    if {family(str(entry["node_name"])) for entry in receiver_entries} != {
        "MID360_GUARD",
        "D435I_CAMERA",
        "CAMERA_MOUNT_BRACKET",
        "CAMERA_CARRIER_PLATE",
        "CAMERA_RECEIVER_YOKE",
        "CAMERA_FASTENERS",
    }:
        raise ValueError("D435i-to-S410 receiver diagnostic nodes are incomplete")
    document = App.newDocument("D435i_To_S410_Receiver_Diagnostic")
    try:
        add_manifest_meshes(document, receiver_entries)
        document.recompute()
        view = configure_view()
        save_view(
            view,
            "viewAxonometric",
            "d435i-mount-to-s410-isometric.png",
            0.76,
        )
        for object_ in document.Objects:
            object_.ViewObject.Visibility = family(object_.Label) not in {
                "D435I_CAMERA",
                "CAMERA_MOUNT_BRACKET",
            }
        document.recompute()
        save_view(
            view,
            "viewAxonometric",
            "d435i-receiver-to-s410-isometric.png",
            0.76,
        )
        save_view(
            view,
            "viewTop",
            "d435i-receiver-to-s410-top.png",
            0.80,
        )
    finally:
        App.closeDocument(document.Name)

    printable_entries = [
        entry
        for entry in manifest["printable_assembled"]
        if family(str(entry["node_name"]))
        in {
            "FRONT_CAMERA_BAR",
            "CAMERA_MOUNT_BRACKET",
            "CAMERA_CARRIER_PLATE",
            "CAMERA_FASTENERS",
        }
    ]
    if {family(str(entry["node_name"])) for entry in printable_entries} != {
        "FRONT_CAMERA_BAR",
        "CAMERA_MOUNT_BRACKET",
        "CAMERA_CARRIER_PLATE",
        "CAMERA_FASTENERS",
    }:
        raise ValueError("Printable D435i assembly nodes are incomplete")
    document = App.newDocument("D435i_Printable_Diagnostic")
    try:
        add_manifest_meshes(document, printable_entries)
        document.recompute()
        view = configure_view()
        save_view(
            view,
            "viewAxonometric",
            "d435i-printable-isometric.png",
            0.76,
        )
        save_view(
            view,
            "viewRight",
            "d435i-printable-front.png",
            0.80,
        )
    finally:
        App.closeDocument(document.Name)


def render_factory_interface_diagnostic(
    manifest: dict[str, object],
) -> None:
    interface_families = {
        "FACTORY_INTERFACE",
        "FACTORY_INTERFACE_CONNECTORS",
        "FACTORY_INTERFACE_VENTS",
    }
    entries = [
        entry
        for entry in manifest["visual_reference"]
        if family(str(entry["node_name"])) in interface_families
    ]
    document = App.newDocument("Factory_Interface_Diagnostic")
    try:
        add_manifest_meshes(document, entries)
        document.recompute()
        view = configure_view()
        save_view(
            view,
            "viewAxonometric",
            "factory-interface-isometric.png",
            1.40,
        )
        save_view(
            view,
            "viewFront",
            "factory-interface-front.png",
            0.84,
        )
        save_view(
            view,
            "viewRear",
            "factory-interface-rear.png",
            0.84,
        )
        save_view(
            view,
            "viewLeft",
            "factory-interface-left.png",
            0.84,
        )
        save_view(
            view,
            "viewRight",
            "factory-interface-right.png",
            0.84,
        )
        save_view(
            view,
            "viewTop",
            "factory-interface-top.png",
            0.84,
        )
    finally:
        App.closeDocument(document.Name)


def render_layout(manifest: dict[str, object]) -> None:
    document = App.newDocument("Lite3_Printable_Layout")
    try:
        add_manifest_meshes(document, manifest["layout"])
        document.recompute()
        view = configure_view()
        save_view(
            view,
            "viewTop",
            "printable-layout-top.png",
            0.93,
        )
        save_view(
            view,
            "viewAxonometric",
            "printable-layout-isometric.png",
            0.90,
        )
    finally:
        App.closeDocument(document.Name)


def render_body_diagnostic(manifest: dict[str, object]) -> None:
    body_families = {"TORSO", "HIP", "THIGH", "SHANK"}
    current_entries = [
        entry
        for entry in manifest["printable_assembled"]
        if family(str(entry["node_name"])) in body_families
    ]
    official_entries = [
        entry
        for entry in manifest["visual_reference"]
        if family(str(entry["node_name"])) in body_families
    ]
    document = App.newDocument("Lite3_Printable_Body_Diagnostic")
    try:
        add_manifest_meshes(document, current_entries)
        document.recompute()
        view = configure_view()
        save_view(
            view,
            "viewAxonometric",
            "body-diagnostic-current-printable-isometric.png",
            0.84,
        )
        save_view(
            view,
            "viewLeft",
            "body-diagnostic-current-printable-left.png",
            0.90,
        )
    finally:
        App.closeDocument(document.Name)

    document = App.newDocument("Lite3_Official_Body_Diagnostic")
    try:
        add_manifest_meshes(document, official_entries)
        document.recompute()
        view = configure_view()
        save_view(
            view,
            "viewAxonometric",
            "body-diagnostic-official-source-isometric.png",
            0.84,
        )
        save_view(
            view,
            "viewLeft",
            "body-diagnostic-official-source-left.png",
            0.90,
        )
    finally:
        App.closeDocument(document.Name)


def render_and_quit() -> None:
    exit_code = 0
    try:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        if not RENDER_MANIFEST.is_file():
            raise FileNotFoundError(RENDER_MANIFEST)
        with RENDER_MANIFEST.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
        render_visual_reference(manifest)
        render_printable_assembly(manifest)
        render_d435i_diagnostic(manifest)
        render_factory_interface_diagnostic(manifest)
        render_layout(manifest)
        render_body_diagnostic(manifest)
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        QtCore.QCoreApplication.exit(exit_code)


QtCore.QTimer.singleShot(500, render_and_quit)
