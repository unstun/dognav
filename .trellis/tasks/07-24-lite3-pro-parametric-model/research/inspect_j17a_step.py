#!/usr/bin/env python3
"""Report cylindrical faces in the related-source J17A STEP geometry."""

from __future__ import annotations

from pathlib import Path

import Part


REPO_ROOT = Path(__file__).resolve().parents[4]
STEP_PATH = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/"
    "source/original/1T21-J17A-lidar base.STEP"
)


def rounded_xyz(vector: object) -> tuple[float, float, float]:
    return (
        round(float(vector.x), 4),
        round(float(vector.y), 4),
        round(float(vector.z), 4),
    )


shape = Part.read(str(STEP_PATH))
print(
    "shape",
    {
        "solids": len(shape.Solids),
        "faces": len(shape.Faces),
        "edges": len(shape.Edges),
        "bounds_mm": [
            round(shape.BoundBox.XMin, 4),
            round(shape.BoundBox.XMax, 4),
            round(shape.BoundBox.YMin, 4),
            round(shape.BoundBox.YMax, 4),
            round(shape.BoundBox.ZMin, 4),
            round(shape.BoundBox.ZMax, 4),
        ],
    },
)

for face_index, face in enumerate(shape.Faces, start=1):
    surface = face.Surface
    if not all(
        hasattr(surface, attribute)
        for attribute in ("Radius", "Axis", "Center")
    ):
        continue
    bounds = face.BoundBox
    print(
        "cylinder",
        {
            "face": face_index,
            "radius_mm": round(float(surface.Radius), 4),
            "axis": rounded_xyz(surface.Axis),
            "center_mm": rounded_xyz(surface.Center),
            "bounds_mm": [
                round(bounds.XMin, 4),
                round(bounds.XMax, 4),
                round(bounds.YMin, 4),
                round(bounds.YMax, 4),
                round(bounds.ZMin, 4),
                round(bounds.ZMax, 4),
            ],
            "area_mm2": round(float(face.Area), 4),
        },
    )
