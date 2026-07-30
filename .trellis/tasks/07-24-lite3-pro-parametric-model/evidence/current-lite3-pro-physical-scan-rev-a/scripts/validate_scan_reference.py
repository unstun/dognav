#!/usr/bin/env python3
"""Validate the archived physical scan and all reference-only derivatives."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "2026-07-30-user-glb-scan"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(condition: bool, label: str, checks: list[dict]) -> None:
    checks.append({"label": label, "passed": bool(condition)})


def count_obj(path: Path) -> tuple[int, int]:
    vertices = faces = 0
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            vertices += line.startswith("v ")
            faces += line.startswith("f ")
    return vertices, faces


def main() -> None:
    checks: list[dict] = []
    index = json.loads((SOURCE / "source_index.json").read_text())
    archive = SOURCE / index["archive"]["name"]
    glb = SOURCE / index["glb"]["name"]
    check(sha256(archive) == index["archive"]["sha256"], "source ZIP SHA-256", checks)
    check(sha256(glb) == index["glb"]["sha256"], "source GLB SHA-256", checks)
    with glb.open("rb") as stream:
        magic, version, declared_length = struct.unpack("<4sII", stream.read(12))
    check(magic == b"glTF" and version == 2, "GLB 2.0 header", checks)
    check(declared_length == glb.stat().st_size, "GLB declared length", checks)

    inspection = json.loads((ROOT / "inspection" / "scan-inspection.json").read_text())
    check(inspection["counts"]["vertices"] == 353508, "raw vertex count", checks)
    check(inspection["counts"]["triangles"] == 617023, "raw triangle count", checks)
    check(inspection["counts"]["images"] == 2, "embedded texture count", checks)

    orientation = json.loads((ROOT / "inspection" / "orientation-contract.json").read_text())
    span = orientation["fit"]["enclosure_top_0p1_to_99p9_span_mm"]
    check(195.0 <= span[0] <= 205.0, "scan scale from enclosure length", checks)
    check(103.0 <= span[1] <= 113.0, "scan scale from enclosure width", checks)
    check(orientation["standard_frame"]["x"] == "+front", "front-axis label", checks)
    check(orientation["standard_frame"]["y"].startswith("+left"), "right-handed lateral-axis label", checks)

    required_renders = [
        ROOT / "renders" / "scan-photo-orientation-comparison.png",
        ROOT / "renders" / "oriented-robot" / "00-corrected-four-view-contact-sheet.png",
        ROOT / "renders" / "mount-area" / "01-upper-body-metric-top.png",
        ROOT / "renders" / "mount-area" / "02-front-deck-metric-top.png",
        ROOT / "renders" / "mount-area" / "06-scan-photo-scaffold-registration.png",
        ROOT / "renders" / "mount-area" / "07-compute-enclosure-top-footprint-mount-frame.png",
    ]
    for render in required_renders:
        check(render.is_file() and render.stat().st_size > 10000, f"render exists: {render.name}", checks)

    footprint = json.loads((ROOT / "inspection" / "compute-enclosure-footprint.json").read_text())
    recess = footprint["recess_detection"]
    check(footprint["status"] == "two_front_recesses_recovered_from_scan", "two-recess footprint status", checks)
    check(recess["nominal_shoulder_x_mm"] == -130, "recess shoulder X", checks)
    check(recess["nominal_inner_y_mm"] == [-42, 44], "recess inner Y edges", checks)
    check(len(footprint["nominal_footprint_polygon_mm"]) == 8, "notched footprint vertex count", checks)

    mesh_dir = ROOT / "derived" / "upper-body-mesh-reference"
    report = json.loads((mesh_dir / "mesh-export-report.json").read_text())
    obj = mesh_dir / "lite3-pro-oriented-upper-body-reference-mm.obj"
    obj_vertices, obj_faces = count_obj(obj)
    check(obj_vertices == report["textured_obj"]["vertices"], "OBJ vertex count", checks)
    check(obj_faces == report["textured_obj"]["triangles"], "OBJ triangle count", checks)
    stl = mesh_dir / "lite3-pro-oriented-upper-body-reference-3mm-lightweight.stl"
    with stl.open("rb") as stream:
        stream.read(80)
        stl_triangles = struct.unpack("<I", stream.read(4))[0]
    check(stl.stat().st_size == 84 + stl_triangles * 50, "binary STL byte count", checks)
    check(stl_triangles == report["lightweight_stl"]["triangles"], "lightweight STL triangle count", checks)
    check(report["lightweight_stl"]["manufacturing_use"] is False, "STL manufacturing prohibition", checks)

    result = {
        "status": "passed" if all(item["passed"] for item in checks) else "failed",
        "checks": checks,
        "claim": "Oriented scan accepted for visual, envelope, and collision reference only.",
        "manufacturing_release": False,
    }
    output = ROOT / "inspection" / "quality-validation.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
