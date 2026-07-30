#!/usr/bin/env python3
"""Export a cropped, oriented Lite3 upper-body mesh reference.

The textured OBJ preserves scan detail for visual review. The 3 mm
vertex-clustered STL is a lightweight Fusion reference and is explicitly not a
printable/manufacturing body.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

import numpy as np

from glb_scan import GlbDocument, combined_cloud
from orient_lite3_scan import fit_orientation, roi_mask, transform_to_standard


CROP_MM = {"x": [-300.0, 320.0], "y": [-210.0, 210.0], "z": [300.0, 455.0]}
STL_GRID_MM = 3.0


def within_crop(points: np.ndarray) -> np.ndarray:
    return (
        (points[:, 0] >= CROP_MM["x"][0])
        & (points[:, 0] <= CROP_MM["x"][1])
        & (points[:, 1] >= CROP_MM["y"][0])
        & (points[:, 1] <= CROP_MM["y"][1])
        & (points[:, 2] >= CROP_MM["z"][0])
        & (points[:, 2] <= CROP_MM["z"][1])
    )


def write_obj(
    output_dir: Path,
    document: GlbDocument,
    clouds: list[dict],
    fit: dict,
    floor: float,
) -> dict:
    obj_path = output_dir / "lite3-pro-oriented-upper-body-reference-mm.obj"
    mtl_path = output_dir / "lite3-pro-oriented-upper-body-reference-mm.mtl"
    texture_names = []
    for index in range(len(document.json.get("images", []))):
        name = f"scan-texture-{index}.jpg"
        document.image(index).save(output_dir / name, quality=95, subsampling=0)
        texture_names.append(name)
    with mtl_path.open("w", encoding="utf-8") as stream:
        for index, texture in enumerate(texture_names):
            stream.write(f"newmtl scan_material_{index}\n")
            stream.write("Ka 0.000000 0.000000 0.000000\n")
            stream.write("Kd 1.000000 1.000000 1.000000\n")
            stream.write("Ks 0.000000 0.000000 0.000000\n")
            stream.write(f"map_Kd {texture}\n\n")
    vertex_offset = 0
    triangle_count = 0
    used_vertex_count = 0
    all_geometry = []
    with obj_path.open("w", encoding="utf-8") as stream:
        stream.write("# Current Lite3 Professional scan reference; units = mm\n")
        stream.write("# Visual/collision reference only; not a manufacturing body\n")
        stream.write(f"mtllib {mtl_path.name}\n")
        for primitive_index, cloud in enumerate(clouds):
            points = transform_to_standard(cloud["world_positions"], fit, floor)
            triangles = cloud["indices"].reshape(-1, 3)
            keep = within_crop(points)
            triangles = triangles[keep[triangles].all(axis=1)]
            used, inverse = np.unique(triangles, return_inverse=True)
            local_triangles = inverse.reshape(-1, 3)
            local_points = points[used]
            local_uv = cloud["texcoords"][used] if cloud["texcoords"] is not None else np.zeros((len(used), 2))
            stream.write(f"\no primitive_{primitive_index}\n")
            for x, y, z in local_points:
                stream.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
            for u, v in local_uv:
                stream.write(f"vt {u:.8f} {v:.8f}\n")
            material_index = primitive_index if primitive_index < len(texture_names) else 0
            stream.write(f"usemtl scan_material_{material_index}\n")
            for a, b, c in local_triangles + vertex_offset + 1:
                stream.write(f"f {a}/{a} {b}/{b} {c}/{c}\n")
            vertex_offset += len(local_points)
            triangle_count += len(local_triangles)
            used_vertex_count += len(local_points)
            all_geometry.append((local_points, local_triangles))
    return {
        "obj": str(obj_path),
        "mtl": str(mtl_path),
        "textures": texture_names,
        "vertices": used_vertex_count,
        "triangles": triangle_count,
        "geometry": all_geometry,
    }


def clustered_mesh(geometry: list[tuple[np.ndarray, np.ndarray]], grid_mm: float) -> tuple[np.ndarray, np.ndarray]:
    points = []
    triangles = []
    offset = 0
    for local_points, local_triangles in geometry:
        points.append(local_points)
        triangles.append(local_triangles + offset)
        offset += len(local_points)
    points_array = np.vstack(points)
    triangles_array = np.vstack(triangles)
    quantized = np.rint(points_array / grid_mm).astype(np.int32)
    unique_quantized, inverse = np.unique(quantized, axis=0, return_inverse=True)
    simplified = inverse[triangles_array]
    nondegenerate = (
        (simplified[:, 0] != simplified[:, 1])
        & (simplified[:, 1] != simplified[:, 2])
        & (simplified[:, 0] != simplified[:, 2])
    )
    simplified = simplified[nondegenerate]
    # Deduplicate triangles irrespective of winding only for the duplicate key;
    # preserve the first triangle's original winding for its STL normal.
    keys = np.sort(simplified, axis=1)
    _, unique_index = np.unique(keys, axis=0, return_index=True)
    simplified = simplified[np.sort(unique_index)]
    vertices = unique_quantized.astype(np.float64) * grid_mm
    a, b, c = vertices[simplified[:, 0]], vertices[simplified[:, 1]], vertices[simplified[:, 2]]
    normals = np.cross(b - a, c - a)
    area2 = np.linalg.norm(normals, axis=1)
    return vertices, simplified[area2 > 1e-9]


def write_binary_stl(path: Path, vertices: np.ndarray, triangles: np.ndarray) -> None:
    a, b, c = vertices[triangles[:, 0]], vertices[triangles[:, 1]], vertices[triangles[:, 2]]
    normals = np.cross(b - a, c - a)
    length = np.linalg.norm(normals, axis=1)
    normals[length > 0] /= length[length > 0, None]
    header = b"Lite3 Pro scan reference; 3 mm clustered; NOT FOR PRINT".ljust(80, b" ")
    with path.open("wb") as stream:
        stream.write(header)
        stream.write(struct.pack("<I", len(triangles)))
        record = np.zeros(
            len(triangles),
            dtype=np.dtype([("normal", "<f4", (3,)), ("a", "<f4", (3,)), ("b", "<f4", (3,)), ("c", "<f4", (3,)), ("attr", "<u2")]),
        )
        record["normal"], record["a"], record["b"], record["c"] = normals, a, b, c
        stream.write(record.tobytes())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    document = GlbDocument.load(args.input)
    raw, _colors, clouds = combined_cloud(document)
    fit = fit_orientation(raw)
    local = roi_mask(raw)
    floor = float(np.percentile(raw[local, 1], 1.0))
    result = write_obj(args.output_dir, document, clouds, fit, floor)
    vertices, triangles = clustered_mesh(result.pop("geometry"), STL_GRID_MM)
    stl_path = args.output_dir / "lite3-pro-oriented-upper-body-reference-3mm-lightweight.stl"
    write_binary_stl(stl_path, vertices, triangles)
    report = {
        "status": "reference_only",
        "source": str(args.input),
        "crop_mm": CROP_MM,
        "textured_obj": result,
        "lightweight_stl": {
            "path": str(stl_path),
            "vertex_cluster_grid_mm": STL_GRID_MM,
            "vertices": int(len(vertices)),
            "triangles": int(len(triangles)),
            "manufacturing_use": False,
        },
        "warning": "Both outputs are scan references. Do not print, tap, or dimension small holes from them.",
    }
    (args.output_dir / "mesh-export-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
