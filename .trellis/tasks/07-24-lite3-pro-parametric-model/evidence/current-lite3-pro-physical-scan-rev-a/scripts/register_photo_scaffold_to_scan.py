#!/usr/bin/env python3
"""Register the photo-measured planar scaffold to the oriented scan.

This is a review overlay, not a receiver fit. The translation is derived from
the independently measured compute-enclosure front edge; Z and all thread
properties remain unknown.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from glb_scan import GlbDocument, combined_cloud
from orient_lite3_scan import ENCLOSURE_TOP_Y, fit_orientation, roi_mask


VIEW_X = (-280.0, 300.0)
VIEW_Y = (-190.0, 190.0)
IMAGE_SIZE = (1800, 1400)
MARGIN = 130


def pixel(x: float, y: float) -> tuple[float, float]:
    width, height = IMAGE_SIZE
    scale = min((width - 2 * MARGIN) / (VIEW_X[1] - VIEW_X[0]), (height - 2 * MARGIN) / (VIEW_Y[1] - VIEW_Y[0]))
    left = (width - (VIEW_X[1] - VIEW_X[0]) * scale) / 2
    top = (height - (VIEW_Y[1] - VIEW_Y[0]) * scale) / 2
    return left + (x - VIEW_X[0]) * scale, top + (VIEW_Y[1] - y) * scale


def dashed_vertical(draw: ImageDraw.ImageDraw, x: float, y0: float, y1: float, fill: tuple, width: int = 4) -> None:
    px, top = pixel(x, y1)
    _, bottom = pixel(x, y0)
    dash = 18
    cursor = top
    while cursor < bottom:
        draw.line((px, cursor, px, min(cursor + dash, bottom)), fill=fill, width=width)
        cursor += dash * 1.7


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("photo_measurements", type=Path)
    parser.add_argument("base_render", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    document = GlbDocument.load(args.input)
    raw, _colors, _clouds = combined_cloud(document)
    fit = fit_orientation(raw)
    top_mask = roi_mask(raw) & (raw[:, 1] >= ENCLOSURE_TOP_Y[0]) & (raw[:, 1] <= ENCLOSURE_TOP_Y[1])
    xz = raw[top_mask][:, [0, 2]]
    centroid = np.asarray(fit["raw_xz_centroid"])
    forward = np.asarray(fit["raw_forward_unit_xz"])
    lateral = np.array([-forward[1], forward[0]])
    scan_x = (xz - centroid) @ forward * 1000.0
    # transform_to_standard negates the rotated lateral coordinate.
    scan_y = -((xz - centroid) @ lateral) * 1000.0
    x_low, x_high = np.percentile(scan_x, [0.1, 99.9])
    y_low, y_high = np.percentile(scan_y, [0.1, 99.9])

    photos = json.loads(args.photo_measurements.read_text())
    measurements = photos["measurements"]
    photo_compute_front = measurements["compute_enclosure_front_x_mm"]
    pitch = measurements["front_pair_lateral_pitch_mm"]
    centre_x = measurements["centre_candidate_axis_x_mm"]
    nose_x = measurements["nose_edge_x_mm"]
    # mount_x = scan_x - scan_mount_origin_x. Requiring the scan enclosure
    # front to equal the photo-frame -100 mm edge gives this translation.
    scan_mount_origin_x = float(x_high - photo_compute_front["value"])
    origin_uncertainty = math.sqrt(photo_compute_front["uncertainty_mm"] ** 2 + 1.0 ** 2)
    pair = [
        {"label": "front_left_axis", "scan_xy_mm": [scan_mount_origin_x, pitch["value"] / 2]},
        {"label": "front_right_axis", "scan_xy_mm": [scan_mount_origin_x, -pitch["value"] / 2]},
    ]
    centre = [scan_mount_origin_x + centre_x["value"], 0.0]
    nose = scan_mount_origin_x + nose_x["value"]
    mount_enclosure = {
        "x": [float(x_low - scan_mount_origin_x), float(x_high - scan_mount_origin_x)],
        "y": [float(y_low), float(y_high)],
    }

    image = Image.open(args.base_render).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    font = ImageFont.load_default(size=20)
    small = ImageFont.load_default(size=17)
    # Scan-derived outer envelope only. The true enclosure footprint contains
    # two front-side recesses and is reconstructed separately as a polygon.
    p0 = pixel(float(x_low), float(y_high))
    p1 = pixel(float(x_high), float(y_low))
    draw.rectangle((*p0, *p1), outline=(217, 72, 44, 220), width=6)
    draw.text((p0[0] + 8, p0[1] + 8), "scan enclosure outer envelope", fill=(170, 48, 28, 255), font=small)
    # Photo-derived axis candidates transformed into the scan frame.
    radius_px = 8.0 * min((IMAGE_SIZE[0] - 2 * MARGIN) / (VIEW_X[1] - VIEW_X[0]), (IMAGE_SIZE[1] - 2 * MARGIN) / (VIEW_Y[1] - VIEW_Y[0]))
    for item in pair:
        px, py = pixel(*item["scan_xy_mm"])
        draw.ellipse((px - radius_px, py - radius_px, px + radius_px, py + radius_px), outline=(0, 103, 190, 255), width=7)
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=(0, 103, 190, 255))
    cx, cy = pixel(*centre)
    draw.ellipse((cx - radius_px, cy - radius_px, cx + radius_px, cy + radius_px), outline=(245, 177, 18, 255), width=7)
    draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(245, 177, 18, 255))
    dashed_vertical(draw, nose, -120.0, 120.0, (0, 150, 136, 220), 5)

    draw.rounded_rectangle((1110, 84, 1755, 250), radius=16, fill=(255, 255, 255, 232), outline=(30, 41, 52, 120), width=2)
    draw.text((1140, 106), "BLUE  photo front-pair candidates (65 mm)", fill=(0, 82, 155, 255), font=font)
    draw.text((1140, 146), "YELLOW  photo centre candidate (-75 mm)", fill=(176, 118, 0, 255), font=font)
    draw.text((1140, 186), "CYAN  photo usable nose edge (+20 mm)", fill=(0, 116, 106, 255), font=font)
    draw.text((1140, 226), "RED  scan enclosure outer envelope", fill=(170, 48, 28, 255), font=font)

    render_path = args.output_root / "renders" / "mount-area" / "06-scan-photo-scaffold-registration.png"
    render_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(render_path)
    report = {
        "status": "planar_candidate_registration_for_human_review",
        "scan_frame": {
            "origin": "compute-enclosure top centroid",
            "units": "mm",
            "x": "+front",
            "y": "+left",
            "z": "+up"
        },
        "mount_frame": {
            "origin": "front small-hole pair midpoint",
            "scan_frame_origin_xy_mm": [scan_mount_origin_x, 0.0],
            "scan_frame_origin_x_uncertainty_mm": origin_uncertainty,
            "z_registration_mm": None,
            "status": "X translation derived from photo-measured enclosure front; Y assumes centreline; Z and receiver geometry remain open"
        },
        "scan_enclosure_top_bounds_mm": {"x": [float(x_low), float(x_high)], "y": [float(y_low), float(y_high)]},
        "mount_frame_enclosure_top_bounds_mm": mount_enclosure,
        "predicted_scan_frame_landmarks_mm": {
            "front_pair": pair,
            "centre_candidate_xy": centre,
            "usable_nose_edge_x": nose
        },
        "enclosure_shape_note": "The plotted red rectangle is the outer envelope, not the true footprint; the true footprint has two front-side recesses.",
        "claim_boundary": "Overlay tests consistency between the photo scaffold and scan envelope. It does not detect or validate receiver holes, threads, depth, or seating Z.",
        "manufacturing_release": False
    }
    report_path = args.output_root / "inspection" / "scan-photo-scaffold-registration.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
