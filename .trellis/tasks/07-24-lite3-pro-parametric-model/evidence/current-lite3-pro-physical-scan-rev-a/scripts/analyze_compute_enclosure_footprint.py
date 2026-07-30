#!/usr/bin/env python3
"""Recover the two-recess compute-enclosure footprint from the oriented scan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from glb_scan import GlbDocument, combined_cloud
from orient_lite3_scan import fit_orientation, roi_mask, transform_to_standard
from render_mount_area import render


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("registration", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    registration = json.loads(args.registration.read_text())
    mount_origin_x = registration["mount_frame"]["scan_frame_origin_xy_mm"][0]
    document = GlbDocument.load(args.input)
    raw, colors, _clouds = combined_cloud(document)
    fit = fit_orientation(raw)
    local = roi_mask(raw)
    floor = float(np.percentile(raw[local, 1], 1.0))
    points = transform_to_standard(raw, fit, floor)
    points[:, 0] -= mount_origin_x
    top_mask = (
        (points[:, 0] >= -330.0)
        & (points[:, 0] <= -80.0)
        & (points[:, 1] >= -80.0)
        & (points[:, 1] <= 80.0)
        & (points[:, 2] >= 435.0)
        & (points[:, 2] <= 450.0)
    )
    top = points[top_mask]
    outer = registration["mount_frame_enclosure_top_bounds_mm"]
    bins = []
    for left in np.arange(-155.0, -99.0, 1.0):
        values = top[(top[:, 0] >= left) & (top[:, 0] < left + 1.0), 1]
        if len(values) >= 20:
            low, high = np.percentile(values, [0.5, 99.5])
            bins.append({"x_center_mm": float(left + 0.5), "count": int(len(values)), "low_y_mm": float(low), "high_y_mm": float(high), "width_mm": float(high - low)})
    shoulder_candidates = []
    for index in range(len(bins) - 2):
        run = bins[index : index + 3]
        if all(item["width_mm"] < 95.0 for item in run):
            shoulder_candidates.append(run[0]["x_center_mm"])
            break
    if not shoulder_candidates:
        raise RuntimeError("Could not locate front recess shoulder")
    detected_shoulder = shoulder_candidates[0]
    nominal_shoulder = round(detected_shoulder)
    front_band = top[(top[:, 0] >= nominal_shoulder + 5.0) & (top[:, 0] <= -105.0), 1]
    inner_low, inner_high = np.percentile(front_band, [0.5, 99.5])
    nominal_inner_low = round(float(inner_low))
    nominal_inner_high = round(float(inner_high))
    outer_low, outer_high = outer["y"]
    report = {
        "schema_version": 1,
        "status": "two_front_recesses_recovered_from_scan",
        "source_glb": str(args.input),
        "mount_frame_registration": str(args.registration),
        "top_surface_band_z_mm": [435.0, 450.0],
        "sample_count": int(len(top)),
        "outer_envelope_mm": outer,
        "recess_detection": {
            "detected_shoulder_x_mm": detected_shoulder,
            "nominal_shoulder_x_mm": nominal_shoulder,
            "nominal_front_x_mm": -100.0,
            "nominal_longitudinal_length_mm": float(-100.0 - nominal_shoulder),
            "inner_y_percentile_mm": [float(inner_low), float(inner_high)],
            "nominal_inner_y_mm": [nominal_inner_low, nominal_inner_high],
            "right_recess_depth_mm": float(nominal_inner_low - outer_low),
            "left_recess_depth_mm": float(outer_high - nominal_inner_high),
            "bin_width_mm": 1.0,
            "change_rule": "first three consecutive X bins with 0.5-to-99.5-percentile width below 95 mm"
        },
        "nominal_footprint_polygon_mm": [
            [outer["x"][0], outer_low],
            [nominal_shoulder, outer_low],
            [nominal_shoulder, nominal_inner_low],
            [-100.0, nominal_inner_low],
            [-100.0, nominal_inner_high],
            [nominal_shoulder, nominal_inner_high],
            [nominal_shoulder, outer_high],
            [outer["x"][0], outer_high]
        ],
        "claim_boundary": "Scan-derived exterior footprint with millimetre-rounded step faces. Corner radii, vertical wall detail, feet, ports, and manufacturing tolerances remain simplified or open.",
        "manufacturing_release": False,
        "x_bin_diagnostics": bins,
    }
    report_path = args.output_root / "inspection" / "compute-enclosure-footprint.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    render(
        points,
        colors,
        args.output_root / "renders" / "mount-area" / "07-compute-enclosure-top-footprint-mount-frame.png",
        "Compute enclosure top surface — mount frame, not rectangular proxy",
        (-330.0, -80.0),
        (-80.0, 80.0),
        (435.0, 450.0),
        5.0,
    )
    print(json.dumps({key: report[key] for key in ["status", "sample_count", "outer_envelope_mm", "recess_detection", "nominal_footprint_polygon_mm"]}, indent=2))


if __name__ == "__main__":
    main()
