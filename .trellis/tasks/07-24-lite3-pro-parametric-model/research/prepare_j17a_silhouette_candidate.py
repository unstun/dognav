#!/usr/bin/env python3
"""Prepare an evidence-only J17A silhouette comparison.

This script does not modify the replica build. It aligns the published J17A
mesh from the historical source-backed assembly to the current J20A placement,
then exports only primary/source geometry for visual comparison.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
REPLICA_ROOT = (
    REPO_ROOT
    / "references/derived/2026-07-24_lite3-lidar-printable-replica"
)
CURRENT_GLB = (
    REPLICA_ROOT / "models/reference/lite3_lidar_1_1_reference.glb"
)
J17A_HISTORY_GLB = (
    REPLICA_ROOT
    / "rebuild-check-j17a-ipc-base/models/reference/"
    "lite3_lidar_1_1_reference.glb"
)
OUTPUT_ROOT = TASK_ROOT / "evidence/j17a-silhouette-candidate"
MESH_ROOT = OUTPUT_ROOT / "meshes"
MANIFEST = OUTPUT_ROOT / "manifest.json"

SOURCE_NODES = [
    "TORSO",
    "FACTORY_INTERFACE",
    "FACTORY_INTERFACE_CONNECTORS",
    "FACTORY_INTERFACE_VENTS",
    "MID360_ADAPTER",
    "MID360_GUARD",
    "MID360_BODY",
    "MID360_HOUSING_EXTERIOR",
    "MID360_OPTICAL_WINDOW",
    "MID360_CONNECTOR",
    "D435I_CAMERA",
]


def world_mesh(scene: trimesh.Scene, node_name: str) -> trimesh.Trimesh:
    transform, geometry_name = scene.graph.get(node_name)
    mesh = scene.geometry[geometry_name].copy()
    mesh.apply_transform(transform)
    return mesh


def export_mm(mesh: trimesh.Trimesh, path: Path) -> dict[str, object]:
    mesh = mesh.copy()
    mesh.apply_scale(1000.0)
    mesh.export(path)
    return {
        "path": str(path.resolve()),
        "bounds_mm": np.asarray(mesh.bounds).round(6).tolist(),
        "extent_mm": np.asarray(mesh.extents).round(6).tolist(),
        "vertex_count": int(len(mesh.vertices)),
        "face_count": int(len(mesh.faces)),
    }


def main() -> None:
    MESH_ROOT.mkdir(parents=True, exist_ok=True)
    current = trimesh.load(CURRENT_GLB, force="scene")
    history = trimesh.load(J17A_HISTORY_GLB, force="scene")

    current_adapter = world_mesh(current, "MID360_ADAPTER")
    history_adapter = world_mesh(history, "MID360_ADAPTER")
    alignment_m = (
        current_adapter.bounding_box.centroid
        - history_adapter.bounding_box.centroid
    )

    entries: list[dict[str, object]] = []
    for node_name in SOURCE_NODES:
        mesh = world_mesh(current, node_name)
        path = MESH_ROOT / f"{node_name}.stl"
        metrics = export_mm(mesh, path)
        entries.append(
            {
                "node_name": node_name,
                "source": "current_source_geometry",
                **metrics,
            }
        )

    j17a = world_mesh(history, "J17A_SENSOR_CARRIER")
    j17a.apply_translation(alignment_m)
    j17a_path = MESH_ROOT / "J17A_SENSOR_CARRIER_CANDIDATE.stl"
    entries.append(
        {
            "node_name": "J17A_SENSOR_CARRIER_CANDIDATE",
            "source": "related_lite3_venture_fast_livo2_source_model",
            **export_mm(j17a, j17a_path),
        }
    )

    manifest = {
        "schema_version": 1,
        "purpose": "evidence_only_j17a_factory_silhouette_comparison",
        "current_glb": str(CURRENT_GLB.resolve()),
        "j17a_history_glb": str(J17A_HISTORY_GLB.resolve()),
        "alignment_method": (
            "rigid translation aligning the J17A-history J20A bounding-box "
            "centroid to the current source-backed J20A bounding-box centroid"
        ),
        "alignment_translation_mm": (alignment_m * 1000.0).round(6).tolist(),
        "forbidden_current_nodes": [
            "CAMERA_MOUNT_BRACKET",
            "CAMERA_CARRIER_PLATE",
            "CAMERA_RECEIVER_YOKE",
            "CAMERA_FASTENERS",
            "FACTORY_LIDAR_MOUNTS",
        ],
        "claim_boundary": (
            "This is an evidence overlay, not an accepted replica revision. "
            "J17A remains related-source candidate geometry."
        ),
        "entries": entries,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"manifest={MANIFEST}")
    print(
        "alignment_translation_mm="
        f"{manifest['alignment_translation_mm']}"
    )
    print(f"mesh_count={len(entries)}")


if __name__ == "__main__":
    main()
