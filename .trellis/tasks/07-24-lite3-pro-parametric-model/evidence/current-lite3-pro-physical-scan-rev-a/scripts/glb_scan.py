#!/usr/bin/env python3
"""Minimal GLB 2.0 reader and textured point renderer for the Lite3 scan.

The implementation deliberately uses only NumPy and Pillow so the evidence can
be reproduced without installing a CAD or mesh-processing package.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942

COMPONENT_DTYPES = {
    5120: np.dtype("<i1"),
    5121: np.dtype("<u1"),
    5122: np.dtype("<i2"),
    5123: np.dtype("<u2"),
    5125: np.dtype("<u4"),
    5126: np.dtype("<f4"),
}

TYPE_COMPONENTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


@dataclass
class GlbDocument:
    path: Path
    json: dict[str, Any]
    binary: bytes

    @classmethod
    def load(cls, path: Path) -> "GlbDocument":
        with path.open("rb") as stream:
            magic, version, total_length = struct.unpack("<4sII", stream.read(12))
            if magic != b"glTF" or version != 2:
                raise ValueError(f"Unsupported GLB header: {magic!r}, version={version}")
            chunks: dict[int, bytes] = {}
            while stream.tell() < total_length:
                chunk_length, chunk_type = struct.unpack("<II", stream.read(8))
                chunks[chunk_type] = stream.read(chunk_length)
        if JSON_CHUNK not in chunks or BIN_CHUNK not in chunks:
            raise ValueError("GLB must contain JSON and BIN chunks")
        document = json.loads(chunks[JSON_CHUNK].rstrip(b"\x00 ").decode("utf-8"))
        return cls(path=path, json=document, binary=chunks[BIN_CHUNK])

    def accessor(self, index: int) -> np.ndarray:
        accessor = self.json["accessors"][index]
        view = self.json["bufferViews"][accessor["bufferView"]]
        dtype = COMPONENT_DTYPES[accessor["componentType"]]
        components = TYPE_COMPONENTS[accessor["type"]]
        count = accessor["count"]
        view_offset = view.get("byteOffset", 0)
        accessor_offset = accessor.get("byteOffset", 0)
        offset = view_offset + accessor_offset
        packed_stride = dtype.itemsize * components
        stride = view.get("byteStride", packed_stride)
        if stride == packed_stride:
            array = np.frombuffer(
                self.binary,
                dtype=dtype,
                count=count * components,
                offset=offset,
            ).reshape(count, components)
        else:
            array = np.ndarray(
                shape=(count, components),
                dtype=dtype,
                buffer=self.binary,
                offset=offset,
                strides=(stride, dtype.itemsize),
            )
        return np.asarray(array)

    def image(self, index: int) -> Image.Image:
        image_info = self.json["images"][index]
        view = self.json["bufferViews"][image_info["bufferView"]]
        offset = view.get("byteOffset", 0)
        raw = self.binary[offset : offset + view["byteLength"]]
        return Image.open(io.BytesIO(raw)).convert("RGB")

    def primitive_clouds(self) -> list[dict[str, Any]]:
        clouds: list[dict[str, Any]] = []
        for mesh_index, mesh in enumerate(self.json.get("meshes", [])):
            for primitive_index, primitive in enumerate(mesh.get("primitives", [])):
                attributes = primitive.get("attributes", {})
                positions = self.accessor(attributes["POSITION"]).astype(np.float64)
                texcoords = None
                colors = np.full((len(positions), 3), 205, dtype=np.uint8)
                if "TEXCOORD_0" in attributes and "material" in primitive:
                    texcoords = self.accessor(attributes["TEXCOORD_0"]).astype(np.float64)
                    material = self.json["materials"][primitive["material"]]
                    texture_info = material.get("pbrMetallicRoughness", {}).get("baseColorTexture")
                    if texture_info is not None:
                        texture = self.json["textures"][texture_info["index"]]
                        image = self.image(texture["source"])
                        pixels = np.asarray(image)
                        uv = np.mod(texcoords, 1.0)
                        x = np.clip(np.rint(uv[:, 0] * (pixels.shape[1] - 1)), 0, pixels.shape[1] - 1).astype(np.int64)
                        # glTF texture coordinates use the lower-left convention.
                        y = np.clip(np.rint((1.0 - uv[:, 1]) * (pixels.shape[0] - 1)), 0, pixels.shape[0] - 1).astype(np.int64)
                        colors = pixels[y, x, :3].astype(np.uint8)
                indices = None
                if "indices" in primitive:
                    indices = self.accessor(primitive["indices"]).reshape(-1).astype(np.uint32)
                clouds.append(
                    {
                        "mesh_index": mesh_index,
                        "primitive_index": primitive_index,
                        "positions": positions,
                        "texcoords": texcoords,
                        "colors": colors,
                        "indices": indices,
                    }
                )
        return clouds


def _rotation_matrix_from_quaternion(quaternion: list[float]) -> np.ndarray:
    x, y, z, w = quaternion
    n = math.sqrt(x * x + y * y + z * z + w * w)
    if n == 0:
        return np.eye(4)
    x, y, z, w = x / n, y / n, z / n, w / n
    matrix = np.eye(4)
    matrix[:3, :3] = np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )
    return matrix


def node_matrix(node: dict[str, Any]) -> np.ndarray:
    if "matrix" in node:
        return np.asarray(node["matrix"], dtype=np.float64).reshape(4, 4).T
    transform = np.eye(4)
    if "translation" in node:
        transform[:3, 3] = node["translation"]
    rotation = _rotation_matrix_from_quaternion(node.get("rotation", [0.0, 0.0, 0.0, 1.0]))
    scale = np.diag([*node.get("scale", [1.0, 1.0, 1.0]), 1.0])
    transform[:3, :3] = rotation[:3, :3] @ scale[:3, :3]
    return transform


def world_mesh_transforms(document: GlbDocument) -> dict[int, np.ndarray]:
    result: dict[int, np.ndarray] = {}
    scene_index = document.json.get("scene", 0)
    roots = document.json.get("scenes", [{}])[scene_index].get("nodes", [])

    def visit(index: int, parent: np.ndarray) -> None:
        node = document.json["nodes"][index]
        current = parent @ node_matrix(node)
        if "mesh" in node:
            result[node["mesh"]] = current
        for child in node.get("children", []):
            visit(child, current)

    for root in roots:
        visit(root, np.eye(4))
    return result


def combined_cloud(document: GlbDocument) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    clouds = document.primitive_clouds()
    transforms = world_mesh_transforms(document)
    all_positions = []
    all_colors = []
    for cloud in clouds:
        positions = cloud["positions"]
        homogeneous = np.column_stack([positions, np.ones(len(positions))])
        world = (transforms.get(cloud["mesh_index"], np.eye(4)) @ homogeneous.T).T[:, :3]
        cloud["world_positions"] = world
        all_positions.append(world)
        all_colors.append(cloud["colors"])
    return np.vstack(all_positions), np.vstack(all_colors), clouds


def inspect(document: GlbDocument) -> dict[str, Any]:
    positions, _colors, clouds = combined_cloud(document)
    minimum = positions.min(axis=0)
    maximum = positions.max(axis=0)
    centered = positions - positions.mean(axis=0)
    covariance = np.cov(centered, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    return {
        "source": str(document.path),
        "asset": document.json.get("asset", {}),
        "counts": {
            "scenes": len(document.json.get("scenes", [])),
            "nodes": len(document.json.get("nodes", [])),
            "meshes": len(document.json.get("meshes", [])),
            "primitives": len(clouds),
            "vertices": int(len(positions)),
            "triangles": int(sum(len(c["indices"]) // 3 for c in clouds if c["indices"] is not None)),
            "materials": len(document.json.get("materials", [])),
            "textures": len(document.json.get("textures", [])),
            "images": len(document.json.get("images", [])),
        },
        "bounds_raw_gltf_units": {
            "min": minimum.tolist(),
            "max": maximum.tolist(),
            "size": (maximum - minimum).tolist(),
        },
        "pca": {
            "centroid": positions.mean(axis=0).tolist(),
            "eigenvalues": eigenvalues.tolist(),
            "eigenvectors_columns": eigenvectors.tolist(),
        },
        "node_mesh_transforms": {
            str(index): matrix.tolist() for index, matrix in world_mesh_transforms(document).items()
        },
        "scale_claim": {
            "status": "unverified",
            "note": "glTF nominally uses metres, but scan-export scale must be checked against a measured physical landmark before manufacturing use.",
        },
    }


def render_view(
    positions: np.ndarray,
    colors: np.ndarray,
    horizontal_axis: int,
    vertical_axis: int,
    depth_axis: int,
    camera_sign: int,
    title: str,
    output: Path,
    size: int = 1600,
    unit_label: str = "glTF units",
) -> None:
    margin = 100
    canvas = np.full((size, size, 3), 248, dtype=np.uint8)
    h = positions[:, horizontal_axis]
    v = positions[:, vertical_axis]
    d = positions[:, depth_axis] * camera_sign
    h_min, h_max = np.percentile(h, [0.02, 99.98])
    v_min, v_max = np.percentile(v, [0.02, 99.98])
    span_h = max(h_max - h_min, 1e-12)
    span_v = max(v_max - v_min, 1e-12)
    scale = min((size - 2 * margin) / span_h, (size - 2 * margin) / span_v)
    px = np.rint((h - (h_min + h_max) / 2) * scale + size / 2).astype(np.int32)
    py = np.rint(size / 2 - (v - (v_min + v_max) / 2) * scale).astype(np.int32)
    valid = (px >= margin // 2) & (px < size - margin // 2) & (py >= margin // 2) & (py < size - margin // 2)
    px, py, d, point_colors = px[valid], py[valid], d[valid], colors[valid]

    # Keep the closest point for each pixel, then repeat those visible samples
    # over a 3x3 footprint. Near samples are painted last so they remain visible.
    linear = py.astype(np.int64) * size + px
    order = np.lexsort((-d, linear))
    sorted_linear = linear[order]
    first = np.r_[True, sorted_linear[1:] != sorted_linear[:-1]]
    chosen = order[first]
    chosen = chosen[np.argsort(d[chosen])]
    visible_x, visible_y = px[chosen], py[chosen]
    visible_colors = point_colors[chosen]
    for dy, dx in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        x = visible_x + dx
        y = visible_y + dy
        inside = (x >= 0) & (x < size) & (y >= 0) & (y < size)
        canvas[y[inside], x[inside]] = visible_colors[inside]

    image = Image.fromarray(canvas)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, size, 64), fill=(25, 31, 39))
    draw.text((24, 19), title, fill=(255, 255, 255), font=ImageFont.load_default(size=24))
    precision = 1 if unit_label == "mm" else 4
    draw.text(
        (24, size - 44),
        f"span: {span_h:.{precision}f} x {span_v:.{precision}f} {unit_label}",
        fill=(25, 31, 39),
        font=ImageFont.load_default(size=18),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def render_all(document: GlbDocument, output_dir: Path, size: int) -> None:
    positions, colors, _clouds = combined_cloud(document)
    views = [
        (0, 2, 1, 1, "Original top: camera +Y, screen X/Z", "01-original-top-plus-y.png"),
        (0, 2, 1, -1, "Original bottom: camera -Y, screen X/Z", "02-original-bottom-minus-y.png"),
        (0, 1, 2, 1, "Original side: camera +Z, screen X/Y", "03-original-side-plus-z.png"),
        (0, 1, 2, -1, "Original opposite side: camera -Z, screen X/Y", "04-original-side-minus-z.png"),
        (2, 1, 0, 1, "Original end: camera +X, screen Z/Y", "05-original-end-plus-x.png"),
        (2, 1, 0, -1, "Original opposite end: camera -X, screen Z/Y", "06-original-end-minus-x.png"),
    ]
    paths = []
    for h_axis, v_axis, d_axis, sign, title, name in views:
        path = output_dir / name
        render_view(positions, colors, h_axis, v_axis, d_axis, sign, title, path, size=size)
        paths.append(path)

    thumb_size = 520
    sheet = Image.new("RGB", (thumb_size * 3, thumb_size * 2), (238, 241, 244))
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_size, thumb_size))
        x = (index % 3) * thumb_size + (thumb_size - image.width) // 2
        y = (index // 3) * thumb_size + (thumb_size - image.height) // 2
        sheet.paste(image, (x, y))
    sheet.save(output_dir / "00-original-six-view-contact-sheet.png")

    render_top_height_map(
        positions,
        output_dir / "07-original-top-height-map-with-grid.png",
        size=size,
    )


def render_top_height_map(positions: np.ndarray, output: Path, size: int = 1600) -> None:
    """Render an X/Z occupancy map colored by maximum Y height."""
    margin = 110
    x = positions[:, 0]
    z = positions[:, 2]
    y = positions[:, 1]
    x_min, x_max = positions[:, 0].min(), positions[:, 0].max()
    z_min, z_max = positions[:, 2].min(), positions[:, 2].max()
    span_x = x_max - x_min
    span_z = z_max - z_min
    scale = min((size - 2 * margin) / span_x, (size - 2 * margin) / span_z)
    left = size / 2 - span_x * scale / 2
    top = size / 2 - span_z * scale / 2
    px = np.rint(left + (x - x_min) * scale).astype(np.int32)
    py = np.rint(top + (z_max - z) * scale).astype(np.int32)
    valid = (px >= 0) & (px < size) & (py >= 0) & (py < size)
    px, py, y = px[valid], py[valid], y[valid]
    linear = py.astype(np.int64) * size + px
    order = np.lexsort((-y, linear))
    sorted_linear = linear[order]
    first = np.r_[True, sorted_linear[1:] != sorted_linear[:-1]]
    chosen = order[first]
    height = np.clip(y[chosen] / max(float(y.max()), 1e-12), 0.0, 1.0)
    stops = np.array([0.0, 0.18, 0.42, 0.68, 1.0])
    palette = np.array(
        [
            [224, 229, 234],
            [64, 119, 181],
            [51, 185, 168],
            [242, 196, 64],
            [199, 45, 45],
        ],
        dtype=np.float64,
    )
    rgb = np.column_stack([np.interp(height, stops, palette[:, channel]) for channel in range(3)]).astype(np.uint8)
    canvas = np.full((size, size, 3), 250, dtype=np.uint8)
    visible_x, visible_y = px[chosen], py[chosen]
    for dy, dx in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
        xx, yy = visible_x + dx, visible_y + dy
        inside = (xx >= 0) & (xx < size) & (yy >= 0) & (yy < size)
        canvas[yy[inside], xx[inside]] = rgb[inside]
    image = Image.fromarray(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    font = ImageFont.load_default(size=18)
    # 0.1 glTF-unit grid; labels allow the scan scale and crop to be audited.
    for coordinate in np.arange(math.ceil(x_min * 10) / 10, x_max + 0.001, 0.1):
        xx = left + (coordinate - x_min) * scale
        draw.line((xx, top, xx, top + span_z * scale), fill=(30, 41, 52, 62), width=1)
        draw.text((xx + 2, top + span_z * scale + 8), f"{coordinate:.1f}", fill=(25, 31, 39, 255), font=font)
    for coordinate in np.arange(math.ceil(z_min * 10) / 10, z_max + 0.001, 0.1):
        yy = top + (z_max - coordinate) * scale
        draw.line((left, yy, left + span_x * scale, yy), fill=(30, 41, 52, 62), width=1)
        draw.text((left - 54, yy - 9), f"{coordinate:.1f}", fill=(25, 31, 39, 255), font=font)
    draw.rectangle((0, 0, size, 64), fill=(25, 31, 39, 255))
    draw.text((24, 19), "Original X/Z top height map; grid = 0.1 raw glTF units", fill=(255, 255, 255, 255), font=ImageFont.load_default(size=24))
    draw.text((24, size - 34), "colour = maximum Y height (grey low, red high)", fill=(25, 31, 39, 255), font=font)
    image.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--render-dir", type=Path)
    parser.add_argument("--size", type=int, default=1600)
    args = parser.parse_args()
    document = GlbDocument.load(args.input)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(inspect(document), indent=2, ensure_ascii=False) + "\n")
    if args.render_dir:
        args.render_dir.mkdir(parents=True, exist_ok=True)
        render_all(document, args.render_dir, args.size)


if __name__ == "__main__":
    main()
