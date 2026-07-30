#!/usr/bin/env python3
"""Inspect and tessellate the official FAST-LIVO2 compute-side STEP parts.

Run this file with FreeCAD's ``freecadcmd`` runtime.  It keeps the STEP inputs
unchanged and writes only review meshes plus a geometry manifest.  The output
does not establish an assembly transform or Lite3 Pro fit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import MeshPart
import Part


TASK_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = TASK_ROOT.parents[2]
SOURCE_ROOT = (
    PROJECT_ROOT
    / "references/upstream/"
    "2026-07-24_lite3-venture-fast-livo2-hardware/source/original"
)
OUTPUT_ROOT = TASK_ROOT / "evidence/official-fast-livo2-compute-parts"
MESH_ROOT = OUTPUT_ROOT / "meshes"
MANIFEST = OUTPUT_ROOT / "manifest.json"

JOBS = {
    "BZ20_BACKLOAD_SHELL_SOURCE": "1T21-BZ20-backload shell.STEP",
    "AGX_ORIN_BASE_SOURCE": "AGX-orin-base.STEP",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def vector(value: Any) -> list[float]:
    return [
        round(float(value.x), 6),
        round(float(value.y), 6),
        round(float(value.z), 6),
    ]


def shape_metrics(shape: Part.Shape) -> dict[str, Any]:
    bound = shape.BoundBox
    total_volume = float(sum(solid.Volume for solid in shape.Solids))
    if total_volume > 0.0:
        center_of_mass_mm = [
            round(
                float(
                    sum(
                        solid.CenterOfMass.x * solid.Volume
                        for solid in shape.Solids
                    )
                    / total_volume
                ),
                6,
            ),
            round(
                float(
                    sum(
                        solid.CenterOfMass.y * solid.Volume
                        for solid in shape.Solids
                    )
                    / total_volume
                ),
                6,
            ),
            round(
                float(
                    sum(
                        solid.CenterOfMass.z * solid.Volume
                        for solid in shape.Solids
                    )
                    / total_volume
                ),
                6,
            ),
        ]
    else:
        center_of_mass_mm = [
            round(float(0.5 * (bound.XMin + bound.XMax)), 6),
            round(float(0.5 * (bound.YMin + bound.YMax)), 6),
            round(float(0.5 * (bound.ZMin + bound.ZMax)), 6),
        ]
    cylindrical_faces = [
        face
        for face in shape.Faces
        if getattr(face.Surface, "TypeId", "") == "Part::GeomCylinder"
    ]
    cylinder_axes = []
    for face in cylindrical_faces:
        surface = face.Surface
        cylinder_axes.append(
            {
                "radius_mm": round(float(surface.Radius), 6),
                "axis": vector(surface.Axis),
                "center": vector(surface.Center),
            }
        )
    return {
        "solid_count": len(shape.Solids),
        "shell_count": len(shape.Shells),
        "face_count": len(shape.Faces),
        "edge_count": len(shape.Edges),
        "bbox_min_mm": [
            round(float(bound.XMin), 6),
            round(float(bound.YMin), 6),
            round(float(bound.ZMin), 6),
        ],
        "bbox_max_mm": [
            round(float(bound.XMax), 6),
            round(float(bound.YMax), 6),
            round(float(bound.ZMax), 6),
        ],
        "bbox_size_mm": [
            round(float(bound.XLength), 6),
            round(float(bound.YLength), 6),
            round(float(bound.ZLength), 6),
        ],
        "center_of_mass_mm": center_of_mass_mm,
        "solid_volume_mm3": round(total_volume, 6),
        "cylindrical_face_count": len(cylindrical_faces),
        "cylindrical_faces": cylinder_axes,
    }


def main() -> None:
    MESH_ROOT.mkdir(parents=True, exist_ok=True)
    entries: dict[str, Any] = {}
    for node_name, filename in JOBS.items():
        source = SOURCE_ROOT / filename
        shape = Part.read(str(source))
        solid_shape = Part.makeCompound(list(shape.Solids))
        if solid_shape.isNull():
            raise RuntimeError(f"No source solids found in {source}")
        mesh = MeshPart.meshFromShape(
            Shape=solid_shape,
            LinearDeflection=0.08,
            AngularDeflection=0.17453292519943295,
            Relative=False,
        )
        output = MESH_ROOT / f"{node_name}.stl"
        mesh.write(str(output))
        entries[node_name] = {
            "source_path": str(source.resolve()),
            "source_sha256": sha256(source),
            "source_geometry": shape_metrics(shape),
            "tessellated_geometry": shape_metrics(solid_shape),
            "mesh_path": str(output.resolve()),
            "mesh_size_bytes": output.stat().st_size,
            "mesh_sha256": sha256(output),
            "mesh_point_count": int(mesh.CountPoints),
            "mesh_facet_count": int(mesh.CountFacets),
        }

    manifest = {
        "schema_version": 1,
        "purpose": "official_fast_livo2_compute_part_identity_review",
        "parts": entries,
        "assembly_transform_state": "not_established",
        "claim_boundary": (
            "The meshes are read-only tessellations of the official Lite3 "
            "Venture FAST-LIVO2 BZ20 and AGX-base STEP files. They prove part "
            "geometry only; they do not prove Lite3 Pro placement, the user's "
            "industrial-PC geometry, or a load-rated mounting design."
        ),
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
