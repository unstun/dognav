#!/usr/bin/env python3
"""Tessellate preserved official sensor and compute STEP files for the builder.

Run this script with FreeCAD's Python runtime. It never edits the STEP inputs.
The generated STL files are deterministic intermediate meshes, not new source
evidence and not manufacturing CAD.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import MeshPart
import Part


ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source_cache" / "official_sensor_meshes"
PARAMETERS = ROOT / "print_parameters.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists() and (candidate / "AGENTS.md").is_file():
            return candidate
    raise RuntimeError(f"Could not find repository root above {start}")


def bbox(shape: Part.Shape) -> dict[str, list[float]]:
    box = shape.BoundBox
    return {
        "min_mm": [box.XMin, box.YMin, box.ZMin],
        "max_mm": [box.XMax, box.YMax, box.ZMax],
        "size_mm": [box.XLength, box.YLength, box.ZLength],
    }


def tessellate(
    source: Path,
    output: Path,
    *,
    solids_only: bool,
    solid_indices: list[int] | None,
    shell_indices: list[int] | None,
    linear_deflection_mm: float,
) -> dict[str, Any]:
    shape = Part.read(str(source))
    if shell_indices is not None:
        missing = [
            index for index in shell_indices if index >= len(shape.Shells)
        ]
        if missing:
            raise ValueError(
                f"STEP shell indices {missing} do not exist in {source}"
            )
        tessellation_shape = Part.makeCompound(
            [shape.Shells[index] for index in shell_indices]
        )
    elif solid_indices is not None:
        missing = [
            index for index in solid_indices if index >= len(shape.Solids)
        ]
        if missing:
            raise ValueError(
                f"STEP solid indices {missing} do not exist in {source}"
            )
        tessellation_shape = Part.makeCompound(
            [shape.Solids[index] for index in solid_indices]
        )
    elif solids_only:
        tessellation_shape = Part.makeCompound(list(shape.Solids))
    else:
        tessellation_shape = shape
    if tessellation_shape.isNull():
        raise ValueError(f"Empty STEP shape: {source}")
    mesh = MeshPart.meshFromShape(
        Shape=tessellation_shape,
        LinearDeflection=linear_deflection_mm,
        AngularDeflection=0.17453292519943295,
        Relative=False,
    )
    if mesh.CountFacets <= 0:
        raise ValueError(f"STEP tessellation produced no facets: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    mesh.write(str(output))
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"FreeCAD did not write {output}")
    return {
        "source": str(source),
        "source_sha256": sha256(source),
        "source_solids": len(shape.Solids),
        "source_shells": len(shape.Shells),
        "source_faces": len(shape.Faces),
        "source_bbox": bbox(shape),
        "tessellated_solids_only": solids_only,
        "solid_indices": solid_indices,
        "shell_indices": shell_indices,
        "tessellated_bbox": bbox(tessellation_shape),
        "linear_deflection_mm": linear_deflection_mm,
        "mesh_vertices": mesh.CountPoints,
        "mesh_facets": mesh.CountFacets,
        "output": str(output),
        "output_size_bytes": output.stat().st_size,
        "output_sha256": sha256(output),
    }


def main() -> None:
    with PARAMETERS.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    project = repo_root(ROOT)
    sources = config["sources"]
    jobs = {
        "mid360_full": {
            "source_key": "mid360_step",
            "filename": "mid360_full_official.stl",
            "solids_only": False,
            "solid_indices": None,
            "shell_indices": None,
            "linear_deflection_mm": 0.10,
        },
        "mid360_solids": {
            "source_key": "mid360_step",
            "filename": "mid360_solids_official.stl",
            "solids_only": True,
            "solid_indices": None,
            "shell_indices": None,
            "linear_deflection_mm": 0.10,
        },
        "mid360_optical_window": {
            "source_key": "mid360_step",
            "filename": "mid360_optical_window_official.stl",
            "solids_only": True,
            "solid_indices": [0],
            "shell_indices": None,
            "linear_deflection_mm": 0.05,
        },
        "mid360_body": {
            "source_key": "mid360_step",
            "filename": "mid360_body_official.stl",
            "solids_only": True,
            "solid_indices": [1],
            "shell_indices": None,
            "linear_deflection_mm": 0.05,
        },
        "mid360_connector": {
            "source_key": "mid360_step",
            "filename": "mid360_connector_official.stl",
            "solids_only": True,
            "solid_indices": [2],
            "shell_indices": None,
            "linear_deflection_mm": 0.05,
        },
        "mid360_housing_exterior": {
            "source_key": "mid360_step",
            "filename": "mid360_housing_exterior_official.stl",
            "solids_only": False,
            "solid_indices": None,
            "shell_indices": [21],
            "linear_deflection_mm": 0.05,
        },
        "j20a": {
            "source_key": "j20a_step",
            "filename": "j20a_official.stl",
            "solids_only": True,
            "solid_indices": None,
            "shell_indices": None,
            "linear_deflection_mm": 0.10,
        },
        "j17a": {
            "source_key": "j17a_step",
            "filename": "j17a_official.stl",
            "solids_only": True,
            "solid_indices": None,
            "shell_indices": None,
            "linear_deflection_mm": 0.10,
        },
        "s410": {
            "source_key": "s410_step",
            "filename": "s410_official.stl",
            "solids_only": True,
            "solid_indices": None,
            "shell_indices": None,
            "linear_deflection_mm": 0.10,
        },
        "jetson_agx_orin_module": {
            "source_key": "jetson_agx_orin_module_step",
            "filename": "jetson_agx_orin_module_official.stl",
            "solids_only": True,
            "solid_indices": None,
            "shell_indices": None,
            "linear_deflection_mm": 0.10,
        },
        "agx_orin_base": {
            "source_key": "agx_orin_base_step",
            "filename": "agx_orin_base_official.stl",
            "solids_only": True,
            "solid_indices": None,
            "shell_indices": None,
            "linear_deflection_mm": 0.10,
        },
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "claim_boundary": (
            "Read-only tessellation of official STEP inputs for the printable "
            "replica pipeline; not factory Lite3 assembly CAD."
        ),
        "meshes": {},
    }
    for name, job in jobs.items():
        source_entry = sources[str(job["source_key"])]
        source = (project / source_entry["path"]).resolve()
        if sha256(source) != source_entry["sha256"]:
            raise ValueError(f"Source hash mismatch: {source}")
        report["meshes"][name] = tessellate(
            source,
            CACHE / str(job["filename"]),
            solids_only=bool(job["solids_only"]),
            solid_indices=job["solid_indices"],
            shell_indices=job["shell_indices"],
            linear_deflection_mm=float(job["linear_deflection_mm"]),
        )
        print(
            f"{name}: {report['meshes'][name]['mesh_facets']} facets -> "
            f"{report['meshes'][name]['output']}",
            flush=True,
        )
    report_path = CACHE / "mesh_manifest.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(f"manifest={report_path}", flush=True)


if __name__ == "__main__":
    main()
