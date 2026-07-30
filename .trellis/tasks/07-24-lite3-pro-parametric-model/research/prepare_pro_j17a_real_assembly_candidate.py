#!/usr/bin/env python3
"""Build the evidence-only Lite3 Pro to J17A real-assembly candidate.

Run with FreeCAD's console Python.  The script preserves the reviewed official
FAST-LIVO2 source meshes and adds only a separately named lower print adapter,
two fastener groups, and the nominal Lite3 Pro threaded-receiver proxies.

This is not factory CAD or a load-rated bracket.  It closes the inspectable
mechanical path from the published Lite3 Pro M3 pattern to the actual
transformed J17A M3 holes without inventing the user's industrial PC.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Mesh
import MeshPart
import Part


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
SOURCE_ROOT = TASK_ROOT / "evidence/official-bz20-layout-candidate"
SOURCE_MANIFEST = SOURCE_ROOT / "manifest.json"
OUTPUT_ROOT = TASK_ROOT / "evidence/pro-j17a-real-assembly-candidate"
MODEL_ROOT = OUTPUT_ROOT / "models"
MESH_ROOT = OUTPUT_ROOT / "meshes"
MANIFEST_PATH = OUTPUT_ROOT / "manifest.json"

TORSO_PROXY_SOURCE = (
    REPO_ROOT
    / "references/derived/2026-07-24_lite3-lidar-printable-replica"
    / "models/master_1_1/torso_master_1_1.stl"
)

PRO_PATTERN_CENTER_X_MM = 20.0
PRO_PATTERN_X_MM = 74.0
PRO_PATTERN_Y_MM = 94.0
PRO_AXIS_X_MM = (-17.0, 57.0)
PRO_AXIS_Y_MM = (-47.0, 47.0)
PRO_INTERFACE_Z_MM = 420.158569

# Derived directly from the unchanged J17A STEP mesh currently used by the
# reviewed source stack.  The source M3 axes are X=-51.75/58.25, Y=+/-43,
# Z=0..2.5 under R=diag(1,-1,1), T=[134.601997, 0, 446.0].
J17A_SOURCE_TRANSLATION_MM = (134.601997, 0.0, 446.0)
J17A_AXIS_X_MM = (82.851997, 192.851997)
J17A_AXIS_Y_MM = (-43.0, 43.0)
J17A_SEATING_Z_MM = 446.0
J17A_THREAD_DEPTH_MM = 2.5

SIDE_TRUSS_Y_MM = 55.0
SIDE_TRUSS_WIDTH_MM = 8.0
SIDE_TRUSS_BOTTOM_Z_MM = 423.0
SIDE_TRUSS_TOP_Z_MM = 427.25
SIDE_TRUSS_X_MIN_MM = -17.0
SIDE_TRUSS_X_MAX_MM = 192.851997
CROSS_TIE_X_MM = 65.0

PRO_PAD_RADIUS_MM = 7.0
PRO_PAD_HEIGHT_MM = 6.6
PRO_COUNTERBORE_DIAMETER_MM = 6.2
PRO_CLEARANCE_DIAMETER_MM = 3.4
PRO_SCREW_LENGTH_MM = 8.0
PRO_SCREW_BEARING_Z_MM = PRO_INTERFACE_Z_MM + 3.5
PRO_RECEIVER_DEPTH_MM = 5.0
PRO_RECEIVER_OUTER_DIAMETER_MM = 10.0
PRO_RECEIVER_MINOR_DIAMETER_MM = 2.5

J17A_COLUMN_RADIUS_MM = 5.0
J17A_COLUMN_BOTTOM_Z_MM = 420.75
J17A_COUNTERBORE_DIAMETER_MM = 6.2
J17A_CLEARANCE_DIAMETER_MM = 3.4
J17A_SCREW_LENGTH_MM = 20.0
J17A_SCREW_BEARING_Z_MM = 428.5

M3_SHAFT_DIAMETER_MM = 3.0
M3_HEAD_DIAMETER_MM = 5.5
M3_HEAD_HEIGHT_MM = 3.0
M3_HEX_SOCKET_ACROSS_FLATS_MM = 2.5
M3_HEX_SOCKET_DEPTH_MM = 1.5

SOURCE_NODE_NAMES = (
    "TORSO",
    "J17A_SENSOR_CARRIER_SOURCE",
    "MID360_ADAPTER",
    "MID360_GUARD",
    "MID360_BODY",
    "MID360_HOUSING_EXTERIOR",
    "MID360_OPTICAL_WINDOW",
    "MID360_CONNECTOR",
    "D435I_CAMERA_DIRECT",
    "D435_DIRECT_FASTENER_REFERENCES",
    "BZ20_BACKLOAD_SHELL_SOURCE",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rounded(value: float) -> float:
    return round(float(value), 6)


def shape_metrics(shape: Part.Shape) -> dict[str, object]:
    box = shape.BoundBox
    return {
        "bounds_mm": [
            [rounded(box.XMin), rounded(box.YMin), rounded(box.ZMin)],
            [rounded(box.XMax), rounded(box.YMax), rounded(box.ZMax)],
        ],
        "extent_mm": [
            rounded(box.XLength),
            rounded(box.YLength),
            rounded(box.ZLength),
        ],
        "volume_mm3": rounded(shape.Volume),
        "solid_count": len(shape.Solids),
        "shell_count": len(shape.Shells),
        "is_valid_brep": bool(shape.isValid()),
    }


def export_stl(shape: Part.Shape, path: Path) -> None:
    mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=0.06,
        AngularDeflection=0.20,
        Relative=False,
    )
    mesh.write(str(path))
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"FreeCAD did not write {path}")


def polygon_prism_xy(
    points_xy: list[tuple[float, float]],
    z_min_mm: float,
    height_mm: float,
) -> Part.Shape:
    vectors = [App.Vector(x, y, z_min_mm) for x, y in points_xy]
    vectors.append(vectors[0])
    wire = Part.makePolygon(vectors)
    return Part.Face(wire).extrude(App.Vector(0.0, 0.0, height_mm))


def dogbone_prism(
    start_xy_mm: tuple[float, float],
    end_xy_mm: tuple[float, float],
    width_mm: float,
    z_min_mm: float,
    height_mm: float,
) -> Part.Shape:
    x0, y0 = start_xy_mm
    x1, y1 = end_xy_mm
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length <= 0.0:
        raise ValueError("Dogbone endpoints must differ")
    nx = -dy / length * width_mm / 2.0
    ny = dx / length * width_mm / 2.0
    rectangle = polygon_prism_xy(
        [
            (x0 + nx, y0 + ny),
            (x1 + nx, y1 + ny),
            (x1 - nx, y1 - ny),
            (x0 - nx, y0 - ny),
        ],
        z_min_mm,
        height_mm,
    )
    caps = [
        Part.makeCylinder(
            width_mm / 2.0,
            height_mm,
            App.Vector(x, y, z_min_mm),
        )
        for x, y in (start_xy_mm, end_xy_mm)
    ]
    return rectangle.fuse(caps[0]).fuse(caps[1])


def make_hex_prism(
    x_mm: float,
    y_mm: float,
    z_min_mm: float,
    height_mm: float,
) -> Part.Shape:
    radius = M3_HEX_SOCKET_ACROSS_FLATS_MM / math.sqrt(3.0)
    points = [
        (
            x_mm + radius * math.cos(math.radians(60.0 * index + 30.0)),
            y_mm + radius * math.sin(math.radians(60.0 * index + 30.0)),
        )
        for index in range(6)
    ]
    return polygon_prism_xy(points, z_min_mm, height_mm)


def make_socket_head_screw(
    x_mm: float,
    y_mm: float,
    bearing_z_mm: float,
    shaft_length_mm: float,
    direction: int,
) -> Part.Shape:
    if direction not in (-1, 1):
        raise ValueError("Screw direction must be -1 or +1")
    shaft_radius = M3_SHAFT_DIAMETER_MM / 2.0
    head_radius = M3_HEAD_DIAMETER_MM / 2.0
    if direction > 0:
        shaft_z = bearing_z_mm
        head_z = bearing_z_mm - M3_HEAD_HEIGHT_MM
        socket_z = head_z - 0.05
    else:
        shaft_z = bearing_z_mm - shaft_length_mm
        head_z = bearing_z_mm
        socket_z = (
            bearing_z_mm
            + M3_HEAD_HEIGHT_MM
            - M3_HEX_SOCKET_DEPTH_MM
        )
    shaft = Part.makeCylinder(
        shaft_radius,
        shaft_length_mm,
        App.Vector(x_mm, y_mm, shaft_z),
    )
    head = Part.makeCylinder(
        head_radius,
        M3_HEAD_HEIGHT_MM,
        App.Vector(x_mm, y_mm, head_z),
    )
    socket = make_hex_prism(
        x_mm,
        y_mm,
        socket_z,
        M3_HEX_SOCKET_DEPTH_MM + 0.10,
    )
    return shaft.fuse(head).cut(socket).removeSplitter()


def build_adapter() -> Part.Shape:
    truss_height = SIDE_TRUSS_TOP_Z_MM - SIDE_TRUSS_BOTTOM_Z_MM
    pieces: list[Part.Shape] = []
    for y_sign in (-1.0, 1.0):
        side_y = y_sign * SIDE_TRUSS_Y_MM
        pieces.append(
            dogbone_prism(
                (SIDE_TRUSS_X_MIN_MM, side_y),
                (SIDE_TRUSS_X_MAX_MM, side_y),
                SIDE_TRUSS_WIDTH_MM,
                SIDE_TRUSS_BOTTOM_Z_MM,
                truss_height,
            )
        )
        for x_mm in PRO_AXIS_X_MM:
            pad_y = y_sign * abs(PRO_AXIS_Y_MM[1])
            pieces.append(
                Part.makeCylinder(
                    PRO_PAD_RADIUS_MM,
                    PRO_PAD_HEIGHT_MM,
                    App.Vector(x_mm, pad_y, PRO_INTERFACE_Z_MM),
                )
            )
            pieces.append(
                dogbone_prism(
                    (x_mm, pad_y),
                    (x_mm, side_y),
                    SIDE_TRUSS_WIDTH_MM,
                    SIDE_TRUSS_BOTTOM_Z_MM,
                    truss_height,
                )
            )
        for x_mm in J17A_AXIS_X_MM:
            column_y = y_sign * abs(J17A_AXIS_Y_MM[1])
            pieces.append(
                Part.makeCylinder(
                    J17A_COLUMN_RADIUS_MM,
                    J17A_SEATING_Z_MM - J17A_COLUMN_BOTTOM_Z_MM,
                    App.Vector(x_mm, column_y, J17A_COLUMN_BOTTOM_Z_MM),
                )
            )
            pieces.append(
                dogbone_prism(
                    (x_mm, column_y),
                    (x_mm, side_y),
                    SIDE_TRUSS_WIDTH_MM,
                    SIDE_TRUSS_BOTTOM_Z_MM,
                    truss_height,
                )
            )
    pieces.append(
        dogbone_prism(
            (CROSS_TIE_X_MM, -SIDE_TRUSS_Y_MM),
            (CROSS_TIE_X_MM, SIDE_TRUSS_Y_MM),
            SIDE_TRUSS_WIDTH_MM,
            SIDE_TRUSS_BOTTOM_Z_MM,
            truss_height,
        )
    )

    adapter = pieces[0]
    for piece in pieces[1:]:
        adapter = adapter.fuse(piece)
    adapter = adapter.removeSplitter()

    cutters: list[Part.Shape] = []
    for x_mm in PRO_AXIS_X_MM:
        for y_mm in PRO_AXIS_Y_MM:
            cutters.append(
                Part.makeCylinder(
                    PRO_CLEARANCE_DIAMETER_MM / 2.0,
                    15.0,
                    App.Vector(x_mm, y_mm, PRO_INTERFACE_Z_MM - 2.0),
                )
            )
            cutters.append(
                Part.makeCylinder(
                    PRO_COUNTERBORE_DIAMETER_MM / 2.0,
                    PRO_INTERFACE_Z_MM
                    + PRO_PAD_HEIGHT_MM
                    - PRO_SCREW_BEARING_Z_MM
                    + 1.0,
                    App.Vector(x_mm, y_mm, PRO_SCREW_BEARING_Z_MM),
                )
            )
    for x_mm in J17A_AXIS_X_MM:
        for y_mm in J17A_AXIS_Y_MM:
            cutters.append(
                Part.makeCylinder(
                    J17A_CLEARANCE_DIAMETER_MM / 2.0,
                    J17A_SEATING_Z_MM
                    - J17A_COLUMN_BOTTOM_Z_MM
                    + 4.0,
                    App.Vector(
                        x_mm,
                        y_mm,
                        J17A_COLUMN_BOTTOM_Z_MM - 2.0,
                    ),
                )
            )
            cutters.append(
                Part.makeCylinder(
                    J17A_COUNTERBORE_DIAMETER_MM / 2.0,
                    J17A_SCREW_BEARING_Z_MM
                    - J17A_COLUMN_BOTTOM_Z_MM
                    + 2.0,
                    App.Vector(
                        x_mm,
                        y_mm,
                        J17A_COLUMN_BOTTOM_Z_MM - 2.0,
                    ),
                )
            )
    cutter = cutters[0]
    for item in cutters[1:]:
        cutter = cutter.fuse(item)
    adapter = adapter.cut(cutter).removeSplitter()
    if not adapter.isValid() or len(adapter.Solids) != 1:
        raise RuntimeError(
            "Adapter must be one valid connected BRep solid; "
            f"valid={adapter.isValid()} solids={len(adapter.Solids)}"
        )
    return adapter


def add_metadata(
    obj: App.DocumentObject,
    evidence_class: str,
    role: str,
) -> None:
    obj.addProperty("App::PropertyString", "EvidenceClass", "Evidence")
    obj.EvidenceClass = evidence_class
    obj.addProperty("App::PropertyString", "AssemblyRole", "Evidence")
    obj.AssemblyRole = role


def add_part_object(
    document: App.Document,
    group: App.DocumentObjectGroup,
    name: str,
    label: str,
    shape: Part.Shape,
    evidence_class: str,
    role: str,
) -> App.DocumentObject:
    obj = document.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    add_metadata(obj, evidence_class, role)
    group.addObject(obj)
    return obj


def source_entries() -> list[dict[str, object]]:
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    by_name = {
        str(entry["node_name"]): entry
        for entry in source_manifest["entries"]
    }
    missing = sorted(set(SOURCE_NODE_NAMES) - set(by_name))
    if missing:
        raise RuntimeError(f"Source candidate is missing nodes: {missing}")
    entries: list[dict[str, object]] = []
    for name in SOURCE_NODE_NAMES:
        path = Path(str(by_name[name]["path"])).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        entries.append(
            {
                "node_name": name,
                "role": by_name[name].get("role", "source_geometry"),
                "path": str(path),
                "sha256": sha256(path),
                "bounds_mm": by_name[name]["bounds_mm"],
                "extent_mm": by_name[name]["extent_mm"],
                "watertight": by_name[name]["watertight"],
                "connected_components": by_name[name][
                    "connected_components"
                ],
            }
        )
    return entries


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    MESH_ROOT.mkdir(parents=True, exist_ok=True)

    adapter = build_adapter()
    pro_screw_shapes: list[Part.Shape] = []
    j17a_screw_shapes: list[Part.Shape] = []
    receiver_shapes: list[Part.Shape] = []

    for x_mm in PRO_AXIS_X_MM:
        for y_mm in PRO_AXIS_Y_MM:
            pro_screw_shapes.append(
                make_socket_head_screw(
                    x_mm,
                    y_mm,
                    PRO_SCREW_BEARING_Z_MM,
                    PRO_SCREW_LENGTH_MM,
                    direction=-1,
                )
            )
            receiver_outer = Part.makeCylinder(
                PRO_RECEIVER_OUTER_DIAMETER_MM / 2.0,
                PRO_RECEIVER_DEPTH_MM,
                App.Vector(
                    x_mm,
                    y_mm,
                    PRO_INTERFACE_Z_MM - PRO_RECEIVER_DEPTH_MM,
                ),
            )
            receiver_minor = Part.makeCylinder(
                PRO_RECEIVER_MINOR_DIAMETER_MM / 2.0,
                PRO_RECEIVER_DEPTH_MM + 0.2,
                App.Vector(
                    x_mm,
                    y_mm,
                    PRO_INTERFACE_Z_MM - PRO_RECEIVER_DEPTH_MM - 0.1,
                ),
            )
            receiver_shapes.append(receiver_outer.cut(receiver_minor))

    for x_mm in J17A_AXIS_X_MM:
        for y_mm in J17A_AXIS_Y_MM:
            j17a_screw_shapes.append(
                make_socket_head_screw(
                    x_mm,
                    y_mm,
                    J17A_SCREW_BEARING_Z_MM,
                    J17A_SCREW_LENGTH_MM,
                    direction=1,
                )
            )

    pro_screws = Part.makeCompound(pro_screw_shapes)
    j17a_screws = Part.makeCompound(j17a_screw_shapes)
    receivers = Part.makeCompound(receiver_shapes)

    adapter_stl = MESH_ROOT / "PRO_TO_J17A_OPEN_TRUSS_ADAPTER.stl"
    pro_screw_stl = MESH_ROOT / "PRO_M3X8_FASTENERS.stl"
    j17a_screw_stl = MESH_ROOT / "J17A_M3X20_FASTENERS.stl"
    receiver_stl = MESH_ROOT / "LITE3_PRO_M3_RECEIVER_PROXIES.stl"
    export_stl(adapter, adapter_stl)
    export_stl(pro_screws, pro_screw_stl)
    export_stl(j17a_screws, j17a_screw_stl)
    export_stl(receivers, receiver_stl)

    document = App.newDocument("Lite3_Pro_J17A_Real_Assembly_Candidate")
    source_group = document.addObject(
        "App::DocumentObjectGroup",
        "OfficialSourceGeometry",
    )
    adaptation_group = document.addObject(
        "App::DocumentObjectGroup",
        "PrintAdaptation",
    )
    fastener_group = document.addObject(
        "App::DocumentObjectGroup",
        "Fasteners",
    )
    receiver_group = document.addObject(
        "App::DocumentObjectGroup",
        "ReceiverProxies",
    )

    entries = source_entries()
    for entry in entries:
        name = str(entry["node_name"])
        obj = document.addObject("Mesh::Feature", name)
        obj.Label = name
        obj.Mesh = Mesh.Mesh(str(entry["path"]))
        add_metadata(obj, "source_model", str(entry["role"]))
        source_group.addObject(obj)

    adapter_obj = add_part_object(
        document,
        adaptation_group,
        "PRO_TO_J17A_OPEN_TRUSS_ADAPTER",
        "Pro to J17A open-truss print adapter",
        adapter,
        "print_adaptation",
        "two_interface_structural_adapter",
    )

    for index, shape in enumerate(pro_screw_shapes, start=1):
        add_part_object(
            document,
            fastener_group,
            f"PRO_M3X8_SCREW_{index}",
            f"Pro M3x8 screw {index}",
            shape,
            "official_nominal_plus_candidate_length",
            "top_installed_robot_fastener",
        )
    for index, shape in enumerate(j17a_screw_shapes, start=1):
        add_part_object(
            document,
            fastener_group,
            f"J17A_M3X20_SCREW_{index}",
            f"J17A M3x20 screw {index}",
            shape,
            "source_model_axis_plus_candidate_length",
            "underside_installed_j17a_fastener",
        )
    for index, shape in enumerate(receiver_shapes, start=1):
        add_part_object(
            document,
            receiver_group,
            f"LITE3_PRO_M3_RECEIVER_PROXY_{index}",
            f"Lite3 Pro M3 receiver proxy {index}",
            shape,
            "official_nominal_depth_unpublished",
            "thread_envelope_proxy",
        )

    document.recompute()

    assembly_fcstd = MODEL_ROOT / "lite3_pro_j17a_real_assembly.FCStd"
    document.saveAs(str(assembly_fcstd))
    if not assembly_fcstd.is_file() or assembly_fcstd.stat().st_size == 0:
        raise RuntimeError(f"FreeCAD did not write {assembly_fcstd}")

    adapter_step = MODEL_ROOT / "pro_to_j17a_open_truss_adapter.step"
    adapter_fcstd = MODEL_ROOT / "pro_to_j17a_open_truss_adapter.FCStd"
    Part.export([adapter_obj], str(adapter_step))
    adapter_document = App.newDocument("Pro_To_J17A_Open_Truss_Adapter")
    adapter_copy = adapter_document.addObject(
        "Part::Feature",
        "PRO_TO_J17A_OPEN_TRUSS_ADAPTER",
    )
    adapter_copy.Label = "Pro to J17A open-truss print adapter"
    adapter_copy.Shape = adapter
    add_metadata(
        adapter_copy,
        "print_adaptation",
        "two_interface_structural_adapter",
    )
    adapter_document.recompute()
    adapter_document.saveAs(str(adapter_fcstd))
    App.closeDocument(adapter_document.Name)

    pro_effective_adapter_mm = (
        PRO_SCREW_BEARING_Z_MM - PRO_INTERFACE_Z_MM
    )
    pro_engagement_mm = PRO_SCREW_LENGTH_MM - pro_effective_adapter_mm
    pro_bottom_clearance_mm = (
        PRO_RECEIVER_DEPTH_MM - pro_engagement_mm
    )
    j17a_effective_adapter_mm = (
        J17A_SEATING_Z_MM - J17A_SCREW_BEARING_Z_MM
    )
    j17a_engagement_mm = (
        J17A_SCREW_LENGTH_MM - j17a_effective_adapter_mm
    )
    if not math.isclose(j17a_engagement_mm, J17A_THREAD_DEPTH_MM, abs_tol=1e-6):
        raise RuntimeError("J17A screw engagement must equal source depth")

    generated_entries = [
        {
            "node_name": "PRO_TO_J17A_OPEN_TRUSS_ADAPTER",
            "role": "print_adaptation",
            "path": str(adapter_stl.resolve()),
            "sha256": sha256(adapter_stl),
            **shape_metrics(adapter),
        },
        {
            "node_name": "PRO_M3X8_FASTENERS",
            "role": "four_top_installed_robot_fasteners",
            "path": str(pro_screw_stl.resolve()),
            "sha256": sha256(pro_screw_stl),
            **shape_metrics(pro_screws),
        },
        {
            "node_name": "J17A_M3X20_FASTENERS",
            "role": "four_underside_installed_j17a_fasteners",
            "path": str(j17a_screw_stl.resolve()),
            "sha256": sha256(j17a_screw_stl),
            **shape_metrics(j17a_screws),
        },
        {
            "node_name": "LITE3_PRO_M3_RECEIVER_PROXIES",
            "role": "four_nominal_thread_envelope_proxies",
            "path": str(receiver_stl.resolve()),
            "sha256": sha256(receiver_stl),
            **shape_metrics(receivers),
        },
    ]

    manifest = {
        "schema_version": 1,
        "purpose": "lite3_pro_to_j17a_real_assembly_candidate",
        "coordinate_system": {
            "unit": "millimetre",
            "axes": "X forward, Y left, Z up",
        },
        "source_candidate_manifest": str(SOURCE_MANIFEST.resolve()),
        "pro_interface": {
            "pattern_center_mm": [PRO_PATTERN_CENTER_X_MM, 0.0],
            "pattern_x_by_y_mm": [PRO_PATTERN_X_MM, PRO_PATTERN_Y_MM],
            "axis_centers_mm": [
                [x_mm, y_mm, PRO_INTERFACE_Z_MM]
                for x_mm in PRO_AXIS_X_MM
                for y_mm in PRO_AXIS_Y_MM
            ],
            "thread": "4 x M3; official nominal",
            "thread_depth_state": "not_published",
            "candidate_receiver_depth_mm": PRO_RECEIVER_DEPTH_MM,
        },
        "j17a_interface": {
            "source_transform_translation_mm": list(
                J17A_SOURCE_TRANSLATION_MM
            ),
            "source_transform_rotation": [
                [1.0, 0.0, 0.0],
                [0.0, -1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            "pattern_x_by_y_mm": [110.0, 86.0],
            "axis_centers_mm": [
                [x_mm, y_mm, J17A_SEATING_Z_MM]
                for x_mm in J17A_AXIS_X_MM
                for y_mm in J17A_AXIS_Y_MM
            ],
            "source_thread_depth_mm": J17A_THREAD_DEPTH_MM,
            "stale_rejected_x_axes_mm": [72.676, 182.676],
            "stale_axis_error_mm": 10.175997,
        },
        "adapter_contract": {
            "adapter_identity": "print_adaptation",
            "architecture": (
                "two fixed side trusses plus one narrow boundary cross-tie, "
                "four Pro pads, and four J17A columns; no centre deck"
            ),
            "side_truss_center_y_mm": [
                -SIDE_TRUSS_Y_MM,
                SIDE_TRUSS_Y_MM,
            ],
            "side_truss_z_mm": [
                SIDE_TRUSS_BOTTOM_Z_MM,
                SIDE_TRUSS_TOP_Z_MM,
            ],
            "cross_tie_center_x_mm": CROSS_TIE_X_MM,
            "pro_pad_seating_z_mm": PRO_INTERFACE_Z_MM,
            "j17a_column_seating_z_mm": J17A_SEATING_Z_MM,
            "pro_clearance_diameter_mm": PRO_CLEARANCE_DIAMETER_MM,
            "pro_counterbore_diameter_mm": PRO_COUNTERBORE_DIAMETER_MM,
            "j17a_clearance_diameter_mm": J17A_CLEARANCE_DIAMETER_MM,
            "j17a_counterbore_diameter_mm": (
                J17A_COUNTERBORE_DIAMETER_MM
            ),
            **shape_metrics(adapter),
        },
        "fastener_contract": {
            "pro_to_robot": {
                "count": 4,
                "standard": "ISO 4762 candidate",
                "nominal": "M3x8",
                "direction": "installed downward from adapter top",
                "bearing_z_mm": PRO_SCREW_BEARING_Z_MM,
                "adapter_traversal_mm": rounded(pro_effective_adapter_mm),
                "modeled_receiver_engagement_mm": rounded(
                    pro_engagement_mm
                ),
                "modeled_bottom_clearance_mm": rounded(
                    pro_bottom_clearance_mm
                ),
                "physical_gate": (
                    "confirm actual Lite3 Pro thread depth before hardware use"
                ),
                "installation_step": 3,
            },
            "adapter_to_j17a": {
                "count": 4,
                "standard": "ISO 4762 candidate",
                "nominal": "M3x20",
                "direction": (
                    "installed upward from recessed adapter underside"
                ),
                "bearing_z_mm": J17A_SCREW_BEARING_Z_MM,
                "adapter_traversal_mm": rounded(
                    j17a_effective_adapter_mm
                ),
                "modeled_receiver_engagement_mm": rounded(
                    j17a_engagement_mm
                ),
                "source_receiver_depth_mm": J17A_THREAD_DEPTH_MM,
                "modeled_bottom_clearance_mm": 0.0,
                "installation_step": 1,
            },
        },
        "assembly_order": [
            "Invert J17A and adapter; install four recessed M3x20 screws upward into J17A.",
            "Place the J17A and adapter subassembly on the Lite3 Pro payload surface.",
            "Install four M3x8 screws downward through the adapter into the robot M3 receivers.",
            "Install BZ20 or the measured user industrial PC last, after the robot-side screw heads are no longer needed.",
        ],
        "torso_collision_proxy": {
            "source_path": str(TORSO_PROXY_SOURCE.resolve()),
            "source_sha256": sha256(TORSO_PROXY_SOURCE),
            "translation_mm": [0.0, 0.0, 351.658569],
            "registration": (
                "payload-plane registered collision proxy; not appearance CAD"
            ),
        },
        "editable_outputs": {
            "assembly_fcstd": str(assembly_fcstd.resolve()),
            "assembly_fcstd_sha256": sha256(assembly_fcstd),
            "adapter_fcstd": str(adapter_fcstd.resolve()),
            "adapter_fcstd_sha256": sha256(adapter_fcstd),
            "adapter_step": str(adapter_step.resolve()),
            "adapter_step_sha256": sha256(adapter_step),
            "adapter_stl": str(adapter_stl.resolve()),
            "adapter_stl_sha256": sha256(adapter_stl),
        },
        "industrial_pc_state": (
            "not_modelled; final adapter outline remains pending the user's "
            "measured IPC envelope, holes, connectors, and cable keep-outs"
        ),
        "claim_boundary": (
            "This candidate closes the modeled Lite3 Pro to J17A fastener "
            "path. It is not factory CAD, load-rated hardware, or proof of "
            "fit around the user's unmeasured industrial PC."
        ),
        "entries": entries + generated_entries,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    App.closeDocument(document.Name)

    print(f"manifest={MANIFEST_PATH}", flush=True)
    print(f"assembly_fcstd={assembly_fcstd}", flush=True)
    print(f"adapter_step={adapter_step}", flush=True)
    print(
        "j17a_axis_x_mm="
        f"{list(J17A_AXIS_X_MM)} stale_error_mm=10.175997",
        flush=True,
    )
    print(
        "fastener_engagement_mm="
        f"pro:{pro_engagement_mm:.3f} "
        f"j17a:{j17a_engagement_mm:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
