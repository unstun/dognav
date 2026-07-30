#!/usr/bin/env python3
"""Extract cylindrical interface axes from preserved sensor-side STEP files.

The output is evidence for sensor-side mounting patterns only.  It deliberately
does not create or infer any current-Lite3-Pro chassis receiver.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import Part


PACKAGE_DIR = Path(__file__).resolve().parent
TASK_DIR = PACKAGE_DIR.parents[1]
REPO_ROOT = TASK_DIR.parents[2]
OUTPUT_PATH = PACKAGE_DIR / "raw_cylindrical_interface_axes.json"

SOURCES = {
    "mid360": REPO_ROOT
    / "references/upstream/2026-07-24_livox-mid360-cad/source/original/mid-360-asm.stp",
    "s410": REPO_ROOT
    / "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/source/original/1CA5-S410-Lidar protector.STEP",
    "j20a_reference": REPO_ROOT
    / "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/source/original/1T21-J20A-small lidar base.STEP",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def vector(values: object) -> list[float]:
    return [float(values.x), float(values.y), float(values.z)]


def dot(first: list[float], second: list[float]) -> float:
    return sum(a * b for a, b in zip(first, second))


def subtract(first: list[float], second: list[float]) -> list[float]:
    return [a - b for a, b in zip(first, second)]


def scale(values: list[float], factor: float) -> list[float]:
    return [factor * value for value in values]


def norm(values: list[float]) -> float:
    return math.sqrt(dot(values, values))


def canonical_axis(values: list[float]) -> list[float]:
    length = norm(values)
    if length <= 1.0e-12:
        raise ValueError("Zero-length cylinder axis")
    result = [value / length for value in values]
    for value in result:
        if abs(value) <= 1.0e-9:
            continue
        if value < 0.0:
            result = [-item for item in result]
        break
    return result


def rounded(values: list[float], digits: int = 6) -> list[float]:
    return [round(value, digits) for value in values]


def cylinder_records(shape: Part.Shape) -> list[dict]:
    records: list[dict] = []
    for face_index, face in enumerate(shape.Faces, start=1):
        surface = face.Surface
        if not all(
            hasattr(surface, attribute)
            for attribute in ("Radius", "Axis", "Center")
        ):
            continue
        axis = canonical_axis(vector(surface.Axis))
        center = vector(surface.Center)
        anchor = subtract(center, scale(axis, dot(center, axis)))
        projected_vertices = [
            dot(vector(vertex.Point), axis) for vertex in face.Vertexes
        ]
        bounds = face.BoundBox
        records.append(
            {
                "face": face_index,
                "radius_mm": round(float(surface.Radius), 6),
                "diameter_mm": round(2.0 * float(surface.Radius), 6),
                "axis": rounded(axis),
                "axis_anchor_closest_to_origin_mm": rounded(anchor),
                "axis_projection_span_mm": [
                    round(min(projected_vertices), 6),
                    round(max(projected_vertices), 6),
                ]
                if projected_vertices
                else None,
                "bounds_mm": {
                    "min": rounded([bounds.XMin, bounds.YMin, bounds.ZMin]),
                    "max": rounded([bounds.XMax, bounds.YMax, bounds.ZMax]),
                },
                "area_mm2": round(float(face.Area), 6),
            }
        )
    return records


def group_coaxial(records: list[dict], tolerance_mm: float = 0.02) -> list[dict]:
    groups: list[dict] = []
    for record in records:
        match = None
        for group in groups:
            alignment = abs(dot(record["axis"], group["axis"]))
            anchor_gap = norm(
                subtract(
                    record["axis_anchor_closest_to_origin_mm"],
                    group["axis_anchor_closest_to_origin_mm"],
                )
            )
            if alignment >= 0.999999 and anchor_gap <= tolerance_mm:
                match = group
                break
        if match is None:
            match = {
                "axis": record["axis"],
                "axis_anchor_closest_to_origin_mm": record[
                    "axis_anchor_closest_to_origin_mm"
                ],
                "faces": [],
            }
            groups.append(match)
        match["faces"].append(record)

    for group_index, group in enumerate(groups, start=1):
        group["group"] = group_index
        group["face_indices"] = [face["face"] for face in group["faces"]]
        group["diameters_mm"] = sorted(
            {face["diameter_mm"] for face in group["faces"]}
        )
        spans = [
            face["axis_projection_span_mm"]
            for face in group["faces"]
            if face["axis_projection_span_mm"] is not None
        ]
        group["combined_axis_projection_span_mm"] = (
            [
                round(min(span[0] for span in spans), 6),
                round(max(span[1] for span in spans), 6),
            ]
            if spans
            else None
        )
    return groups


def shape_metrics(shape: Part.Shape) -> dict:
    bounds = shape.BoundBox
    return {
        "shape_type": shape.ShapeType,
        "is_valid": shape.isValid(),
        "solid_count": len(shape.Solids),
        "face_count": len(shape.Faces),
        "bounds_mm": {
            "min": rounded([bounds.XMin, bounds.YMin, bounds.ZMin]),
            "max": rounded([bounds.XMax, bounds.YMax, bounds.ZMax]),
            "size": rounded([bounds.XLength, bounds.YLength, bounds.ZLength]),
        },
    }


def main() -> None:
    missing = [str(path) for path in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing source files: " + ", ".join(missing))

    sources: dict[str, dict] = {}
    for name, path in SOURCES.items():
        shape = Part.read(str(path))
        cylinders = cylinder_records(shape)
        sources[name] = {
            "path": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256(path),
            "geometry": shape_metrics(shape),
            "cylindrical_face_count": len(cylinders),
            "cylindrical_faces": cylinders,
            "coaxial_groups": group_coaxial(cylinders),
        }

    report = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": "raw_sensor_side_axis_extraction",
        "sources": sources,
        "claim_boundary": (
            "Cylinder extraction is source-geometry evidence only. Grouping does "
            "not assign fastener roles, prove modeled threads, authorize screw "
            "lengths, or define any current-Lite3-Pro chassis receiver."
        ),
    }
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        name: {
            "cylindrical_faces": data["cylindrical_face_count"],
            "coaxial_groups": len(data["coaxial_groups"]),
        }
        for name, data in sources.items()
    }, indent=2))


if __name__ == "__main__":
    main()
