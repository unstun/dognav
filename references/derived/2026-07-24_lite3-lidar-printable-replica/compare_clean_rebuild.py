#!/usr/bin/env python3
"""Compare two zero-cache builds of the Lite3 printable replica."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parent
PRIMARY_REPORT = ROOT / "reports" / "build_report.json"
REBUILD_ROOT = Path(
    os.environ.get("LITE3_PRINT_REBUILD_ROOT", ROOT / "rebuild-check")
).resolve()
REBUILD_REPORT = REBUILD_ROOT / "reports" / "build_report.json"
OUTPUT = ROOT / "reports" / "rebuild_comparison.json"
NONDETERMINISTIC_CONTAINER = "lite3_lidar_1_1_reference.3mf"


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def scene_signature(path: Path) -> dict[str, Any]:
    scene = trimesh.load(path, force="scene", process=False)
    geometries = {}
    for name, mesh in sorted(scene.geometry.items()):
        geometries[name] = {
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "bbox_size": mesh.extents.tolist(),
            "volume": float(abs(mesh.volume)),
        }
    return {
        "geometry_count": int(len(scene.geometry)),
        "bbox_size": scene.extents.tolist(),
        "geometries": geometries,
    }


def signatures_equal(first: dict[str, Any], second: dict[str, Any]) -> bool:
    if first["geometry_count"] != second["geometry_count"]:
        return False
    if set(first["geometries"]) != set(second["geometries"]):
        return False
    if not np.allclose(first["bbox_size"], second["bbox_size"], atol=1.0e-9):
        return False
    for name in first["geometries"]:
        a = first["geometries"][name]
        b = second["geometries"][name]
        if a["vertices"] != b["vertices"] or a["faces"] != b["faces"]:
            return False
        if not np.allclose(a["bbox_size"], b["bbox_size"], atol=1.0e-9):
            return False
        if not np.isclose(a["volume"], b["volume"], rtol=1.0e-10, atol=1.0e-10):
            return False
    return True


def main() -> int:
    primary = load(PRIMARY_REPORT)
    rebuild = load(REBUILD_REPORT)
    structural_sections = (
        "master_reconstruction",
        "body_geometry_tracks",
        "print_parts",
        "standing_reference_1_1",
        "joint_holes",
        "assembly_mounts",
        "lidar_geometry_audit",
    )
    structural = {
        "parameters_sha256": (
            primary["parameters_sha256"] == rebuild["parameters_sha256"]
        ),
        "sources": (
            {
                name: source["sha256"]
                for name, source in primary["sources"].items()
            }
            == {
                name: source["sha256"]
                for name, source in rebuild["sources"].items()
            }
        ),
        **{
            section: primary[section] == rebuild[section]
            for section in structural_sections
        },
    }

    primary_outputs = primary["outputs"]
    rebuild_outputs = rebuild["outputs"]
    output_set_equal = set(primary_outputs) == set(rebuild_outputs)
    output_comparison: dict[str, Any] = {}
    exact_hash_matches = 0
    for name in sorted(set(primary_outputs) | set(rebuild_outputs)):
        first = primary_outputs.get(name)
        second = rebuild_outputs.get(name)
        exact = (
            first is not None
            and second is not None
            and first["sha256"] == second["sha256"]
            and first["size_bytes"] == second["size_bytes"]
        )
        if exact:
            exact_hash_matches += 1
        output_comparison[name] = {
            "exact_hash_and_size": exact,
            "primary": first,
            "rebuild": second,
        }

    container_entry = output_comparison[NONDETERMINISTIC_CONTAINER]
    primary_container = Path(container_entry["primary"]["path"])
    rebuild_container = Path(container_entry["rebuild"]["path"])
    primary_signature = scene_signature(primary_container)
    rebuild_signature = scene_signature(rebuild_container)
    container_equivalent = signatures_equal(
        primary_signature,
        rebuild_signature,
    )
    container_entry.update(
        {
            "format_note": (
                "The 3MF XML serialization is not byte deterministic in "
                "trimesh 4.12.2. Geometry count, face/vertex counts, bounds, "
                "and volumes are compared instead."
            ),
            "geometry_equivalent": container_equivalent,
            "primary_scene_signature": primary_signature,
            "rebuild_scene_signature": rebuild_signature,
        }
    )

    expected_exact = len(primary_outputs) - 1
    passed = (
        all(structural.values())
        and output_set_equal
        and exact_hash_matches == expected_exact
        and container_equivalent
    )
    report = {
        "schema_version": 1,
        "artifact_label": "printable_static_replica",
        "passed": passed,
        "primary_report": str(PRIMARY_REPORT),
        "rebuild_report": str(REBUILD_REPORT),
        "structural_sections_equal": structural,
        "output_set_equal": output_set_equal,
        "output_count": len(primary_outputs),
        "exact_hash_and_size_matches": exact_hash_matches,
        "expected_exact_hash_and_size_matches": expected_exact,
        "nondeterministic_container": NONDETERMINISTIC_CONTAINER,
        "nondeterministic_container_geometry_equivalent": container_equivalent,
        "outputs": output_comparison,
    }
    with OUTPUT.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"passed={passed}", flush=True)
    print(
        f"exact_hash_and_size_matches={exact_hash_matches}/{len(primary_outputs)}",
        flush=True,
    )
    print(
        f"container_geometry_equivalent={container_equivalent}",
        flush=True,
    )
    print(f"report={OUTPUT}", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
