#!/usr/bin/env python3
"""Validate the no-IPC Lite3 Pro to Venture J17A adapter candidate.

Run with FreeCADCmd. Autodesk Fusion is the interactive review environment;
this script independently checks the persisted adapter BRep and transformed
J17A mesh used by the Fusion preview.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Mesh
import Part


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
SOURCE_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware"
    / "source/original"
)
MID360_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-24_livox-mid360-cad/source/original"
)
ROBOT_MODEL = (
    REPO_ROOT
    / "references/upstream/2026-07-24_deep-robotics-model/source"
    / "Lite3-official-high-res-factory-stand-fusion-y-up.stl"
)
SOURCE_SCENE = (
    TASK_ROOT / "evidence/official-bz20-layout-candidate/meshes"
)
ADAPTER_ROOT = TASK_ROOT / "evidence/pro-j17a-real-assembly-candidate"
CURRENT_EVIDENCE = (
    TASK_ROOT
    / "evidence/venture-sensor-stack-on-lite3-pro-fusion-candidate"
)
REPORT_PATH = CURRENT_EVIDENCE / "validation_report.json"

ADAPTER_STEP = (
    ADAPTER_ROOT / "models/pro_to_j17a_open_truss_adapter.step"
)
J17A_WORLD_STL = SOURCE_SCENE / "J17A_SENSOR_CARRIER_SOURCE.stl"

EXPECTED_HASHES = {
    SOURCE_ROOT
    / "1T21-J17A-lidar base.STEP": (
        "52f7f991e904d815d78265a6f695124f2f4bb24131b3500e07f44355ebe39490"
    ),
    SOURCE_ROOT
    / "1T21-J20A-small lidar base.STEP": (
        "341b08ca08526e5ee0e9fbeca0bfda9d9970062c6605e979adc52b31955c9bc9"
    ),
    SOURCE_ROOT
    / "1CA5-S410-Lidar protector.STEP": (
        "7fd23a776b45c7d8571ef77ba9e8b05520eced0b97f62487ba03f88bbc9df810"
    ),
    MID360_ROOT
    / "mid-360-asm.stp": (
        "b93e9b51282ed319b6aa755e76a132c0eb03306da5f3b9676bcabf2e2ae25f02"
    ),
    ROBOT_MODEL: (
        "b2a4d7a1551ebac211d7450f8f57c3a2a198d5d36e70b9c75dccea24f9c55e0c"
    ),
}

PRO_PATTERN_MM = (74.0, 94.0)
J17A_PATTERN_MM = (110.0, 86.0)
PRO_AXES_MM = tuple(
    (x_mm, y_mm)
    for x_mm in (-17.0, 57.0)
    for y_mm in (-47.0, 47.0)
)
J17A_AXES_MM = tuple(
    (x_mm, y_mm)
    for x_mm in (82.851997, 192.851997)
    for y_mm in (-43.0, 43.0)
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mesh_to_solid(path: Path) -> Part.Shape:
    mesh = Mesh.Mesh(str(path))
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, 0.03)
    if shape.Solids:
        return shape.Solids[0]
    if len(shape.Shells) != 1:
        raise RuntimeError(
            f"Expected one closed shell in {path}, found {len(shape.Shells)}"
        )
    solid = Part.makeSolid(shape.Shells[0])
    if solid.isNull() or not solid.isValid():
        raise RuntimeError(f"Could not create a valid solid from {path}")
    return solid


def rounded(value: float) -> float:
    return round(float(value), 6)


def main() -> None:
    CURRENT_EVIDENCE.mkdir(parents=True, exist_ok=True)

    source_hashes = {}
    for path, expected in EXPECTED_HASHES.items():
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"Source hash mismatch for {path}: {actual} != {expected}"
            )
        source_hashes[str(path.relative_to(REPO_ROOT))] = actual

    adapter = Part.read(str(ADAPTER_STEP))
    if not adapter.isValid() or len(adapter.Solids) != 1:
        raise RuntimeError(
            "Adapter must be one valid connected BRep solid; "
            f"valid={adapter.isValid()} solids={len(adapter.Solids)}"
        )

    probe_results = {}
    for label, axes in (
        ("pro_74x94", PRO_AXES_MM),
        ("j17a_110x86", J17A_AXES_MM),
    ):
        volumes = []
        for x_mm, y_mm in axes:
            probe = Part.makeCylinder(
                1.5,
                34.0,
                App.Vector(x_mm, y_mm, 416.0),
            )
            volumes.append(rounded(adapter.common(probe).Volume))
        if any(volume > 1e-6 for volume in volumes):
            raise RuntimeError(f"Blocked fastener probe in {label}: {volumes}")
        probe_results[label] = volumes

    j17a = mesh_to_solid(J17A_WORLD_STL)
    j17a_intersection_mm3 = rounded(adapter.common(j17a).Volume)
    j17a_distance_mm = rounded(adapter.distToShape(j17a)[0])
    if j17a_intersection_mm3 > 1e-6:
        raise RuntimeError(
            "Adapter has undeclared positive J17A overlap: "
            f"{j17a_intersection_mm3} mm3"
        )
    if j17a_distance_mm > 1e-5:
        raise RuntimeError(
            "Adapter does not seat on J17A: "
            f"distance={j17a_distance_mm} mm"
        )

    screenshot_names = (
        "full-assembly-isometric.png",
        "full-assembly-robot-z-isometric.png",
        "full-assembly-opaque-robot-z-isometric.png",
        "sensor-stack-adapter-isometric.png",
        "sensor-stack-adapter-robot-z-top.png",
    )
    missing_screenshots = [
        name for name in screenshot_names if not (CURRENT_EVIDENCE / name).is_file()
    ]
    if missing_screenshots:
        raise RuntimeError(f"Missing Fusion screenshots: {missing_screenshots}")

    same_orientation_delta = (
        J17A_PATTERN_MM[0] - PRO_PATTERN_MM[0],
        J17A_PATTERN_MM[1] - PRO_PATTERN_MM[1],
    )
    rotated_delta = (
        J17A_PATTERN_MM[1] - PRO_PATTERN_MM[0],
        J17A_PATTERN_MM[0] - PRO_PATTERN_MM[1],
    )

    box = adapter.BoundBox
    report = {
        "schema_version": 1,
        "status": "pass",
        "purpose": "lite3_pro_to_venture_fast_livo2_no_ipc_fusion_preview",
        "source_hashes": source_hashes,
        "direct_fit": {
            "pro_pattern_xy_mm": list(PRO_PATTERN_MM),
            "j17a_pattern_xy_mm": list(J17A_PATTERN_MM),
            "same_orientation_delta_xy_mm": list(same_orientation_delta),
            "rotated_j17a_delta_xy_mm": list(rotated_delta),
            "direct_bolt_on": False,
            "adapter_required": True,
        },
        "adapter": {
            "source_step": str(ADAPTER_STEP.relative_to(REPO_ROOT)),
            "sha256": sha256(ADAPTER_STEP),
            "valid_brep": bool(adapter.isValid()),
            "solid_count": len(adapter.Solids),
            "shell_count": len(adapter.Shells),
            "bounds_mm": [
                [rounded(box.XMin), rounded(box.YMin), rounded(box.ZMin)],
                [rounded(box.XMax), rounded(box.YMax), rounded(box.ZMax)],
            ],
            "extent_mm": [
                rounded(box.XLength),
                rounded(box.YLength),
                rounded(box.ZLength),
            ],
            "volume_mm3": rounded(adapter.Volume),
            "fastener_axis_probe_intersection_mm3": probe_results,
            "j17a_positive_intersection_mm3": j17a_intersection_mm3,
            "j17a_seating_distance_mm": j17a_distance_mm,
        },
        "fusion_preview": {
            "document_saved": False,
            "source_mesh_body_count": 9,
            "adapter_brep_body_count": 1,
            "excluded": ["BZ20", "AGX", "industrial_pc", "factory_Interface"],
            "screenshots": list(screenshot_names),
        },
        "claim_boundary": (
            "The source sensor stack and nominal adapter are geometrically "
            "assembled without an industrial PC. The local Lite3 mesh has no "
            "payload threads. Physical hole spacing, thread depth, datum, "
            "material strength, cable clearance, and robot safety are not "
            "validated."
        ),
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
