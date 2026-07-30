"""Validate the current-Pro physical-photo measurement gate and proxy linkage."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


GATE_DIR = Path(__file__).resolve().parent
TASK_DIR = GATE_DIR.parents[1]
SOURCE_DIR = GATE_DIR / "source/2026-07-30-user-physical-measurements"
INDEX_PATH = SOURCE_DIR / "source_index.json"
MEASUREMENTS_PATH = GATE_DIR / "measurement_results.json"
PARAMETERS_PATH = GATE_DIR / "parameters.json"
PROXY_DIR = TASK_DIR / "evidence/current-lite3-pro-measured-proxy-rev-a"
PROXY_VALIDATION_PATH = PROXY_DIR / "validation.json"
SCAN_DIR = TASK_DIR / "evidence/current-lite3-pro-scan-registered-interface-rev-b"
SCAN_PARAMETERS_PATH = SCAN_DIR / "parameters.json"
SCAN_VALIDATION_PATH = SCAN_DIR / "validation.json"
UPPER_VALIDATION_PATH = (
    TASK_DIR / "evidence/current-lite3-pro-source-upper-assembly-rev-b/validation.json"
)
D435I_VALIDATION_PATH = (
    TASK_DIR / "evidence/current-lite3-pro-d435i-support-study-rev-b/validation.json"
)
REQUEST_PATH = GATE_DIR / "receiver_measurement_request.json"
CARD_PATH = GATE_DIR / "renders/current-lite3-pro-receiver-measurement-card-rev-b.png"
OUTPUT_PATH = GATE_DIR / "quality_validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    measurements = json.loads(MEASUREMENTS_PATH.read_text(encoding="utf-8"))
    parameters = json.loads(PARAMETERS_PATH.read_text(encoding="utf-8"))
    proxy = json.loads(PROXY_VALIDATION_PATH.read_text(encoding="utf-8"))
    scan_parameters = json.loads(SCAN_PARAMETERS_PATH.read_text(encoding="utf-8"))
    scan_validation = json.loads(SCAN_VALIDATION_PATH.read_text(encoding="utf-8"))
    upper_validation = json.loads(UPPER_VALIDATION_PATH.read_text(encoding="utf-8"))
    d435i_validation = json.loads(D435I_VALIDATION_PATH.read_text(encoding="utf-8"))
    measurement_request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))

    with Image.open(CARD_PATH) as card:
        card_pixels = list(card.size)

    source_checks = []
    for entry in index["files"]:
        path = SOURCE_DIR / entry["stored_name"]
        with Image.open(path) as image:
            pixels = list(image.size)
        source_checks.append(
            {
                "stored_name": entry["stored_name"],
                "exists": path.is_file(),
                "sha256_matches": sha256(path) == entry["sha256"],
                "pixels_match": pixels == entry["pixels"],
            }
        )

    front_axes = measurements["derived_geometry"]["front_pair_axes_mm"]
    lateral_pitch = abs(front_axes[0][1] - front_axes[1][1])
    measurement_values = measurements["measurements"]
    parameter_geometry = parameters["photo_measured_geometry"]
    receiver_points = parameters["physical_receiver_inventory"]["points"]
    proxy_outputs = proxy["outputs"]
    proxy_hash_checks = {
        name: sha256(PROXY_DIR / data["path"]) == data["sha256"]
        for name, data in proxy_outputs.items()
    }
    scan_hash_checks = {
        name: sha256(SCAN_DIR / data["path"]) == data["sha256"]
        for name, data in scan_validation["outputs"].items()
    }
    current_keepout = parameters["compute_enclosure_keepout"]
    scan_enclosure = scan_parameters["compute_enclosure"]
    required_receiver_fields = set(
        parameters["physical_receiver_inventory"]["required_point_fields"]
    )
    requested_points = measurement_request["receiver_points"]

    checks = {
        "source_file_count_is_ten": len(index["files"]) == 10,
        "all_source_files_exist": all(item["exists"] for item in source_checks),
        "all_source_hashes_match": all(item["sha256_matches"] for item in source_checks),
        "all_source_pixel_dimensions_match": all(item["pixels_match"] for item in source_checks),
        "declared_duplicate_is_byte_identical": sha256(SOURCE_DIR / "photo-07.jpg") == sha256(SOURCE_DIR / "photo-08.jpg"),
        "front_pair_pitch_is_65_mm": abs(lateral_pitch - 65.0) < 1.0e-9,
        "front_pair_pitch_matches_parameter_file": abs(parameter_geometry["front_pair_lateral_pitch_mm"] - lateral_pitch) < 1.0e-9,
        "centre_candidate_axis_matches": parameter_geometry["centre_candidate_axis_mm"] == [-75.0, 0.0, 0.0],
        "compute_enclosure_front_matches": parameter_geometry["compute_enclosure_front_x_mm"] == -100.0,
        "enclosure_nominal_dimensions_match": [
            measurement_values["compute_enclosure_length_mm"]["value"],
            measurement_values["compute_enclosure_width_mm"]["value"],
            measurement_values["compute_enclosure_height_mm"]["value"],
        ] == [200.0, 100.0, 50.0],
        "three_visible_axes_recorded": len(receiver_points) == 3 and parameters["physical_receiver_inventory"]["measured_axis_count"] == 3,
        "no_receiver_accepted": parameters["physical_receiver_inventory"]["accepted_count"] == 0,
        "all_thread_and_depth_fields_remain_null": all(point["thread"] is None and point["usable_depth_mm"] is None for point in receiver_points),
        "all_receiver_material_and_load_path_fields_remain_open": all(
            point["receiver_material"] is None
            and point["threaded_insert_present"] is None
            and point["onward_load_path"] is None
            for point in receiver_points
        ),
        "receiver_rows_contain_every_required_field": all(
            required_receiver_fields.issubset(point) for point in receiver_points
        ),
        "printable_geometry_remains_blocked": parameters["release_gate"]["printable_geometry_allowed"] is False,
        "proxy_validation_pass": proxy["pass"] is True,
        "proxy_output_hashes_match": all(proxy_hash_checks.values()),
        "proxy_contains_no_stl": not any(PROXY_DIR.rglob("*.stl")),
        "scan_registered_interface_validation_pass": scan_validation["pass"] is True,
        "scan_registered_output_hashes_match": all(scan_hash_checks.values()),
        "measurement_gate_uses_scan_rev_b_nominal_footprint": (
            current_keepout["nominal_footprint_polygon_mm"]
            == scan_enclosure["scan_registered_nominal_footprint_polygon_mm"]
        ),
        "measurement_gate_uses_scan_rev_b_expanded_keepout": (
            current_keepout["expanded_proxy_bounds_mm"]
            == scan_enclosure["expanded_collision_keepout_bounds_mm"]
        ),
        "two_front_recesses_are_explicit": (
            len(current_keepout["nominal_footprint_polygon_mm"]) == 8
            and current_keepout["front_side_recesses"]["longitudinal_length_mm"] == 30.0
        ),
        "current_upper_and_d435i_studies_pass": (
            upper_validation["pass"] is True and d435i_validation["pass"] is True
        ),
        "measurement_request_has_a_b_c_receiver_points": (
            [point["callout"] for point in requested_points] == ["A", "B", "C"]
            and [point["label"] for point in requested_points]
            == ["front_left_axis", "front_right_axis", "centre_rear_candidate_axis"]
        ),
        "measurement_request_axes_match_parameter_file": (
            [point["axis_mm"] for point in requested_points]
            == [[point["x_mm"], point["y_mm"], point["seating_z_mm"]] for point in receiver_points]
        ),
        "measurement_request_keeps_every_receiver_open": (
            all(point["status"] == "open" for point in requested_points)
            and measurement_request["release_gate"]["accepted_receiver_count"] == 0
            and measurement_request["release_gate"]["printable_geometry_allowed"] is False
        ),
        "measurement_request_includes_clearance_sweep": (
            measurement_request["clearance_sweep"]["callout"] == "D"
            and measurement_request["clearance_sweep"]["status"] == "open"
        ),
        "measurement_card_exists_and_is_1800_by_1200": (
            CARD_PATH.is_file() and card_pixels == [1800, 1200]
        ),
    }
    report = {
        "schema_version": 4,
        "stage": "experiment_and_analysis",
        "status": "photo_and_scan_registered_measurement_gate_pass_receiver_contract_open",
        "source_checks": source_checks,
        "proxy_hash_checks": proxy_hash_checks,
        "scan_hash_checks": scan_hash_checks,
        "measurement_card": {
            "path": str(CARD_PATH.relative_to(GATE_DIR)),
            "sha256": sha256(CARD_PATH),
            "bytes": CARD_PATH.stat().st_size,
            "pixels": card_pixels,
        },
        "checks": checks,
        "pass": all(checks.values()),
        "remaining_gates": [
            "front-pair thread designation and usable depth",
            "centre visible axis receiver role, thread, depth, material, and load path",
            "compute-enclosure foot, vent, connector, cable, and cover-service sweeps",
            "human review of the selected receiver set before printable geometry",
        ],
        "claim_boundary": "This quality pass verifies photo preservation, scan Rev B two-recess geometry, conservative keep-out propagation, current upper/D435i study linkage, and release-gate enforcement. It does not validate a fastener, load-bearing adapter, physical fit, or print release.",
    }
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
