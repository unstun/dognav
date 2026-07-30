#!/usr/bin/env python3
"""Extract dual-track Lite3 GLB objects as indexed PLY inputs for FreeCAD."""

from __future__ import annotations

import json
from pathlib import Path
import re

import trimesh


ROOT = Path(__file__).resolve().parent
VISUAL_REFERENCE_GLB = (
    ROOT / "models" / "reference" / "lite3_lidar_1_1_reference.glb"
)
PRINTABLE_ASSEMBLED_GLB = (
    ROOT / "models" / "reference" / "lite3_lidar_1_4_assembled.glb"
)
LAYOUT_GLB = (
    ROOT / "models" / "reference" / "lite3_lidar_1_4_print_layout.glb"
)
CACHE = ROOT / "evidence" / "render_cache"
MANIFEST = CACHE / "manifest.json"


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def extract_scene(path: Path, output_directory: Path) -> list[dict[str, object]]:
    scene = trimesh.load(path, force="scene", process=False)
    output_directory.mkdir(parents=True, exist_ok=True)
    entries = []
    for node_name in sorted(scene.graph.nodes_geometry):
        transform, geometry_name = scene.graph[node_name]
        mesh = scene.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        mesh.apply_scale(1000.0)
        output = output_directory / f"{safe_name(node_name)}.ply"
        mesh.export(output, file_type="ply", encoding="binary_little_endian")
        entries.append(
            {
                "node_name": node_name,
                "geometry_name": geometry_name,
                "path": str(output),
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
            }
        )
        print(f"render_mesh={output}", flush=True)
    return entries


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    visual_entries = extract_scene(
        VISUAL_REFERENCE_GLB,
        CACHE / "visual_reference",
    )
    printable_entries = extract_scene(
        PRINTABLE_ASSEMBLED_GLB,
        CACHE / "printable_assembled",
    )
    layout_entries = extract_scene(LAYOUT_GLB, CACHE / "layout")
    with MANIFEST.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "schema_version": 1,
                "visual_reference": visual_entries,
                "printable_assembled": printable_entries,
                "layout": layout_entries,
            },
            handle,
            indent=2,
        )
        handle.write("\n")
    print(f"manifest={MANIFEST}", flush=True)


if __name__ == "__main__":
    main()
