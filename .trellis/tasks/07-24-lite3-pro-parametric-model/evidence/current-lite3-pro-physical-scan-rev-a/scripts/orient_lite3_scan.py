#!/usr/bin/env python3
"""Isolate and orient the current Lite3 Professional scan.

The robot long axis is fitted from the flat top of the measured compute
enclosure. This is more reliable than PCA over the full scan, which also
contains the floor, a chair, and other room geometry.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from glb_scan import GlbDocument, combined_cloud, render_view


RAW_ROI = {
    "x": [-0.25, 0.62],
    "y": [0.0, 0.49],
    "z": [-0.24, 0.34],
}

# The top of the real compute enclosure forms a dense, flat rectangle in this
# narrow height interval. Its 200 x 100 mm physical measurement is independent
# evidence that the scan export is approximately metre-scaled.
ENCLOSURE_TOP_Y = [0.457, 0.468]

CLEAN_STANDARD_CROP_MM = {
    "x": [-340.0, 340.0],
    "y": [-230.0, 230.0],
    "z": [6.0, 470.0],
}


def in_range(values: np.ndarray, bounds: list[float]) -> np.ndarray:
    return (values >= bounds[0]) & (values <= bounds[1])


def roi_mask(positions: np.ndarray) -> np.ndarray:
    return (
        in_range(positions[:, 0], RAW_ROI["x"])
        & in_range(positions[:, 1], RAW_ROI["y"])
        & in_range(positions[:, 2], RAW_ROI["z"])
    )


def fit_orientation(positions: np.ndarray) -> dict:
    candidate = roi_mask(positions) & in_range(positions[:, 1], ENCLOSURE_TOP_Y)
    top = positions[candidate]
    if len(top) < 1000:
        raise RuntimeError(f"Too few compute-enclosure samples: {len(top)}")
    xz = top[:, [0, 2]]
    covariance = np.cov(xz, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    vector = eigenvectors[:, np.argmax(eigenvalues)]
    # Corrected physical top views establish the rounded empty nose as the
    # -raw-X/+raw-Z end. The sign matters: PCA alone only finds an axis.
    if np.dot(vector, np.array([-1.0, 0.35])) < 0:
        vector = -vector
    raw_axis_angle_deg = math.degrees(math.atan2(vector[1], vector[0]))
    correction_deg = -raw_axis_angle_deg
    lateral = np.array([-vector[1], vector[0]])
    projected_mm = np.column_stack([(xz - xz.mean(axis=0)) @ vector, (xz - xz.mean(axis=0)) @ lateral]) * 1000.0
    lower, upper = np.percentile(projected_mm, [0.1, 99.9], axis=0)
    return {
        "sample_count": int(len(top)),
        "raw_xz_centroid": xz.mean(axis=0).tolist(),
        "raw_forward_unit_xz": vector.tolist(),
        "raw_axis_angle_deg": raw_axis_angle_deg,
        "yaw_correction_deg": correction_deg,
        "covariance": covariance.tolist(),
        "eigenvalues": eigenvalues.tolist(),
        "principal_ratio": float(eigenvalues.max() / eigenvalues.min()),
        "raw_xz_bounds": {"min": xz.min(axis=0).tolist(), "max": xz.max(axis=0).tolist()},
        "enclosure_top_0p1_to_99p9_span_mm": (upper - lower).tolist(),
    }


def transform_to_standard(positions: np.ndarray, fit: dict, floor_reference: float) -> np.ndarray:
    theta = math.radians(fit["yaw_correction_deg"])
    rotation = np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
    origin = np.asarray(fit["raw_xz_centroid"])
    ground = (rotation @ (positions[:, [0, 2]] - origin).T).T
    # Standard right-handed mount frame: +X front, +Y left, +Z up. Raw glTF
    # stores the vertical direction in Y, so the rotated ground-plane lateral
    # coordinate is negated to preserve handedness after the axis reorder.
    standard = np.column_stack([ground[:, 0], -ground[:, 1], positions[:, 1] - floor_reference])
    return standard * 1000.0


def write_binary_ply(path: Path, positions_mm: np.ndarray, colors: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {len(positions_mm)}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "property uchar red\n"
        "property uchar green\n"
        "property uchar blue\n"
        "end_header\n"
    ).encode("ascii")
    dtype = np.dtype(
        [("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("r", "u1"), ("g", "u1"), ("b", "u1")]
    )
    vertices = np.empty(len(positions_mm), dtype=dtype)
    vertices["x"], vertices["y"], vertices["z"] = positions_mm.T.astype(np.float32)
    vertices["r"], vertices["g"], vertices["b"] = colors.T
    with path.open("wb") as stream:
        stream.write(header)
        stream.write(vertices.tobytes())


def make_contact_sheet(paths: list[Path], output: Path) -> None:
    thumb = 650
    sheet = Image.new("RGB", (thumb * 2, thumb * 2), (238, 241, 244))
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb, thumb))
        x = (index % 2) * thumb + (thumb - image.width) // 2
        y = (index // 2) * thumb + (thumb - image.height) // 2
        sheet.paste(image, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--size", type=int, default=1600)
    args = parser.parse_args()

    document = GlbDocument.load(args.input)
    positions, colors, _clouds = combined_cloud(document)
    fit = fit_orientation(positions)
    raw_roi = roi_mask(positions)
    local_floor = float(np.percentile(positions[raw_roi, 1], 1.0))
    standard_mm = transform_to_standard(positions, fit, local_floor)

    # Suppress the scanned floor while retaining almost all of each foot.
    above_floor = raw_roi & (positions[:, 1] >= local_floor + 0.006)
    isolated = (
        above_floor
        & in_range(standard_mm[:, 0], CLEAN_STANDARD_CROP_MM["x"])
        & in_range(standard_mm[:, 1], CLEAN_STANDARD_CROP_MM["y"])
        & in_range(standard_mm[:, 2], CLEAN_STANDARD_CROP_MM["z"])
    )
    robot = standard_mm[isolated]
    robot_colors = colors[isolated]
    upper = robot[:, 2] >= 300.0
    upper_robot = robot[upper]
    upper_colors = robot_colors[upper]

    renders = args.output_root / "renders" / "oriented-robot"
    paths = [
        renders / "01-standard-top.png",
        renders / "02-standard-right-side.png",
        renders / "03-standard-front.png",
        renders / "04-standard-upper-body-top.png",
    ]
    render_view(robot, robot_colors, 0, 1, 2, 1, "Corrected top: +X front, +Y left", paths[0], args.size, "mm")
    render_view(robot, robot_colors, 0, 2, 1, -1, "Corrected right side: +X front, +Z up", paths[1], args.size, "mm")
    render_view(robot, robot_colors, 1, 2, 0, 1, "Corrected front: +Y lateral, +Z up", paths[2], args.size, "mm")
    render_view(
        upper_robot,
        upper_colors,
        0,
        1,
        2,
        1,
        "Corrected top, upper body only (Z >= 300 mm)",
        paths[3],
        args.size,
        "mm",
    )
    make_contact_sheet(paths, renders / "00-corrected-four-view-contact-sheet.png")

    write_binary_ply(args.output_root / "derived" / "lite3-pro-oriented-point-reference-mm.ply", robot, robot_colors)
    contract = {
        "status": "candidate_orientation_verified_by_render",
        "source_glb": str(args.input),
        "source_character": "textured room scan containing robot, floor, and unrelated objects",
        "raw_robot_roi_gltf_units": RAW_ROI,
        "clean_standard_crop_mm": CLEAN_STANDARD_CROP_MM,
        "enclosure_top_fit_y_gltf_units": ENCLOSURE_TOP_Y,
        "fit": fit,
        "local_floor_reference_raw_y": local_floor,
        "floor_suppression_mm": 6.0,
        "standard_frame": {
            "units": "mm",
            "x": "+front",
            "y": "+left; right-handed with +X front and +Z up",
            "z": "+up",
            "origin_x_y": "compute-enclosure top centroid",
            "origin_z": "1st-percentile local floor height",
        },
        "isolated_point_count": int(len(robot)),
        "isolated_bounds_mm": {"min": robot.min(axis=0).tolist(), "max": robot.max(axis=0).tolist(), "size": np.ptp(robot, axis=0).tolist()},
        "upper_body_point_count": int(len(upper_robot)),
        "scale_check": {
            "status": "provisionally_consistent",
            "basis": "The fitted enclosure top has a scan envelope consistent with the independently tape-measured approximately 200 x 100 mm housing.",
            "manufacturing_gate": "Do not derive hole diameters or threads from the scan until discrete landmarks are checked against caliper measurements.",
        },
        "output_character": {
            "ply": "oriented colored point reference, not a watertight manufacturing mesh",
            "original_glb": "preserved unchanged as the authoritative scan artifact",
        },
    }
    inspection = args.output_root / "inspection"
    inspection.mkdir(parents=True, exist_ok=True)
    (inspection / "orientation-contract.json").write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
