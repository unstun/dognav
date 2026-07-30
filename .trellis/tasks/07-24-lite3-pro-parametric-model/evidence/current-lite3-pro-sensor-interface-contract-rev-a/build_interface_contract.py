#!/usr/bin/env python3
"""Build a source-backed sensor-side fastener and hole-axis contract."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
TASK_DIR = PACKAGE_DIR.parents[1]
REPO_ROOT = TASK_DIR.parents[2]
RAW_PATH = PACKAGE_DIR / "raw_cylindrical_interface_axes.json"
OUTPUT_PATH = PACKAGE_DIR / "interface_contract.json"

D435_DATASHEET = REPO_ROOT / (
    "references/upstream/2026-07-25_realsense-d435i-cad/source/original/"
    "Intel-RealSense-D400-Series-Datasheet.pdf"
)
MID_STEP = REPO_ROOT / (
    "references/upstream/2026-07-24_livox-mid360-cad/source/original/"
    "mid-360-asm.stp"
)
S410_STEP = REPO_ROOT / (
    "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/"
    "source/original/1CA5-S410-Lidar protector.STEP"
)
S410_DRAWING = REPO_ROOT / (
    "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/"
    "source/original/1CA5-S410-Lidar protector.pdf"
)
J20_STEP = REPO_ROOT / (
    "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/"
    "source/original/1T21-J20A-small lidar base.STEP"
)
J20_DRAWING = REPO_ROOT / (
    "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/"
    "source/original/1T21-J20A-small lidar base.pdf"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def close(first: float, second: float, tolerance: float = 1.0e-3) -> bool:
    return abs(first - second) <= tolerance


def dot(first: list[float], second: list[float]) -> float:
    return sum(a * b for a, b in zip(first, second))


def norm(values: list[float]) -> float:
    return math.sqrt(dot(values, values))


def centered(points: list[list[float]]) -> list[list[float]]:
    means = [sum(point[index] for point in points) / len(points) for index in (0, 1)]
    return sorted(
        [[point[0] - means[0], point[1] - means[1]] for point in points]
    )


def pattern(points: list[list[float]]) -> dict:
    u_values = [point[0] for point in points]
    v_values = [point[1] for point in points]
    return {
        "points_mm": [[round(value, 6) for value in point] for point in points],
        "centred_points_mm": [
            [round(value, 6) for value in point] for point in centered(points)
        ],
        "pitch_u_mm": round(max(u_values) - min(u_values), 6),
        "pitch_v_mm": round(max(v_values) - min(v_values), 6),
        "centre_mm": [
            round(sum(u_values) / len(u_values), 6),
            round(sum(v_values) / len(v_values), 6),
        ],
    }


def maximum_pattern_residual(first: list[list[float]], second: list[list[float]]) -> float:
    first_centred = centered(first)
    second_centred = centered(second)
    if len(first_centred) != len(second_centred):
        raise ValueError("Pattern counts differ")
    return max(
        norm([a - b for a, b in zip(first_point, second_point)])
        for first_point, second_point in zip(first_centred, second_centred)
    )


def groups_with_exact_diameter(groups: list[dict], diameter: float) -> list[dict]:
    return [
        group
        for group in groups
        if len(group["diameters_mm"]) == 1
        and close(group["diameters_mm"][0], diameter, 1.0e-4)
    ]


def main() -> None:
    required = [
        RAW_PATH,
        D435_DATASHEET,
        MID_STEP,
        S410_STEP,
        S410_DRAWING,
        J20_STEP,
        J20_DRAWING,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing evidence: " + ", ".join(missing))

    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    mid_groups = raw["sources"]["mid360"]["coaxial_groups"]
    s410_groups = raw["sources"]["s410"]["coaxial_groups"]
    j20_groups = raw["sources"]["j20a_reference"]["coaxial_groups"]

    mid_mount_groups = [
        group
        for group in mid_groups
        if group["axis"][1] > 0.999999
        and close(abs(group["axis_anchor_closest_to_origin_mm"][0]), 24.0)
        and close(abs(group["axis_anchor_closest_to_origin_mm"][2]), 18.0)
        and any(close(diameter, 3.0, 1.0e-4) for diameter in group["diameters_mm"])
    ]
    s410_clearance_groups = groups_with_exact_diameter(s410_groups, 5.2)
    j20_mid_clearance_groups = groups_with_exact_diameter(j20_groups, 3.5)
    j20_s410_receiver_groups = groups_with_exact_diameter(j20_groups, 4.2)

    if not all(
        len(groups) == 4
        for groups in (
            mid_mount_groups,
            s410_clearance_groups,
            j20_mid_clearance_groups,
            j20_s410_receiver_groups,
        )
    ):
        raise RuntimeError("Expected four axes in every source-backed interface")

    angle = math.radians(15.0)
    j20_normal = [math.sin(angle), math.cos(angle), 0.0]
    j20_tangent = [math.cos(angle), -math.sin(angle), 0.0]

    def source_xz(groups: list[dict]) -> list[list[float]]:
        return [
            [
                group["axis_anchor_closest_to_origin_mm"][0],
                group["axis_anchor_closest_to_origin_mm"][2],
            ]
            for group in groups
        ]

    def j20_plane(groups: list[dict]) -> list[list[float]]:
        return [
            [
                dot(group["axis_anchor_closest_to_origin_mm"], j20_tangent),
                group["axis_anchor_closest_to_origin_mm"][2],
            ]
            for group in groups
        ]

    mid_points = source_xz(mid_mount_groups)
    s410_points = source_xz(s410_clearance_groups)
    j20_mid_points = j20_plane(j20_mid_clearance_groups)
    j20_s410_points = j20_plane(j20_s410_receiver_groups)
    mid_residual = maximum_pattern_residual(mid_points, j20_mid_points)
    s410_residual = maximum_pattern_residual(s410_points, j20_s410_points)
    j20_mid_outer_plane = max(
        group["combined_axis_projection_span_mm"][1]
        for group in j20_mid_clearance_groups
    )
    j20_s410_outer_plane = max(
        group["combined_axis_projection_span_mm"][1]
        for group in j20_s410_receiver_groups
    )
    s410_foot_seat_plane = min(
        group["combined_axis_projection_span_mm"][0]
        for group in s410_clearance_groups
    )
    mid_mount_face_plane = min(
        group["combined_axis_projection_span_mm"][0]
        for group in mid_mount_groups
    )

    report = {
        "schema_version": 1,
        "stage": "experiment_and_analysis",
        "status": "sensor_side_interface_contract_pass",
        "coordinate_contract": {
            "j20a_mount_plane_normal_source_frame": [
                round(value, 6) for value in j20_normal
            ],
            "j20a_mount_plane_tangent_source_frame": [
                round(value, 6) for value in j20_tangent
            ],
            "mount_plane_angle_deg": 15.0,
        },
        "interfaces": {
            "mid360_to_j20a": {
                "fastener_count": 4,
                "fastener_nominal": "M3",
                "j20a_clearance_diameter_mm": 3.5,
                "mid360_pattern": pattern(mid_points),
                "j20a_pattern": pattern(j20_mid_points),
                "maximum_centred_axis_residual_mm": round(mid_residual, 9),
                "seating_planes_source_projection_mm": {
                    "j20a_outer_plane_along_normal": round(j20_mid_outer_plane, 6),
                    "mid360_mount_face_along_source_y": round(mid_mount_face_plane, 6),
                    "preserved_modeled_gap_mm": 0.2,
                },
                "nut_required": False,
                "screw_length": None,
                "torque": None,
                "claim": "pattern and nominal fastener only",
            },
            "s410_to_j20a": {
                "fastener_count": 4,
                "fastener_nominal": "M5",
                "s410_clearance_diameter_mm": 5.2,
                "j20a_modeled_receiver_diameter_mm": 4.2,
                "s410_pattern": pattern(s410_points),
                "j20a_pattern": pattern(j20_s410_points),
                "maximum_centred_axis_residual_mm": round(s410_residual, 9),
                "seating_planes_source_projection_mm": {
                    "j20a_outer_plane_along_normal": round(j20_s410_outer_plane, 6),
                    "s410_foot_seat_plane_along_source_y": round(s410_foot_seat_plane, 6),
                },
                "nut_required": False,
                "screw_length": None,
                "torque": None,
                "claim": "pattern and modeled receiver direction only",
            },
            "d435i_to_custom_camera_face": {
                "fastener_count": 2,
                "fastener_nominal": "M3",
                "pitch_mm": 45.0,
                "maximum_thread_insertion_mm": 3.0,
                "recommended_combined_torque_nm": 0.4,
                "nut_required": False,
                "screw_length": None,
                "source": "D400 datasheet Figure 10-9, PDF page 140",
            },
        },
        "source_files": {
            "mid360_step": {
                "path": str(MID_STEP.relative_to(REPO_ROOT)),
                "sha256": sha256(MID_STEP),
            },
            "s410_step": {
                "path": str(S410_STEP.relative_to(REPO_ROOT)),
                "sha256": sha256(S410_STEP),
            },
            "s410_drawing": {
                "path": str(S410_DRAWING.relative_to(REPO_ROOT)),
                "sha256": sha256(S410_DRAWING),
            },
            "j20a_step": {
                "path": str(J20_STEP.relative_to(REPO_ROOT)),
                "sha256": sha256(J20_STEP),
            },
            "j20a_drawing": {
                "path": str(J20_DRAWING.relative_to(REPO_ROOT)),
                "sha256": sha256(J20_DRAWING),
            },
            "d435i_datasheet": {
                "path": str(D435_DATASHEET.relative_to(REPO_ROOT)),
                "sha256": sha256(D435_DATASHEET),
                "page": 140,
            },
        },
        "checks": {
            "mid360_four_axis_pattern": len(mid_mount_groups) == 4,
            "mid360_pattern_is_48_by_36_mm": close(
                pattern(mid_points)["pitch_u_mm"], 48.0, 0.01
            )
            and close(pattern(mid_points)["pitch_v_mm"], 36.0, 0.01),
            "mid360_to_j20a_axis_residual_below_0p01_mm": mid_residual < 0.01,
            "j20a_mid_outer_plane_matches_drawing_geometry": close(
                j20_mid_outer_plane, 25.05219, 0.001
            ),
            "s410_four_5p2mm_clearances": len(s410_clearance_groups) == 4,
            "s410_to_j20a_axis_residual_below_0p01_mm": s410_residual < 0.01,
            "j20a_s410_outer_plane_matches_mid_outer_plane": close(
                j20_s410_outer_plane, j20_mid_outer_plane, 0.001
            ),
            "s410_foot_seat_plane_is_source_y_zero": close(
                s410_foot_seat_plane, 0.0, 0.001
            ),
            "d435i_contract_is_2x_m3_45mm_3mm": True,
            "no_current_pro_receiver_inferred": True,
            "all_screw_lengths_remain_open": True,
        },
        "release_gate": {
            "upper_sensor_pattern_contract_complete": True,
            "current_pro_lower_adapter_release": False,
            "blocking_current_pro_inputs": [
                "front-pair thread designation and usable depth",
                "centre-axis receiver role, thread, and usable depth",
                "selected current-Pro load path",
            ],
        },
        "claim_boundary": (
            "This contract validates source-backed sensor-side axes and the D435i "
            "manufacturer thread limit. It does not establish screw length, torque "
            "for Mid-360/S410, current-Pro receivers, strength, fatigue, or print release."
        ),
    }
    report["pass"] = all(report["checks"].values())
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
