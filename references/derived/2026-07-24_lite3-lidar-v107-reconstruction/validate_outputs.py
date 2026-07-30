#!/usr/bin/env python3
"""Validate generated Lite3 LiDAR reconstruction records and reproducibility."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


REQUIRED_MODELS = (
    "lite3_lidar_v107_reconstruction.FCStd",
    "lite3_lidar_v107_upper_module.step",
    "lite3_lidar_v107_upper_module.stl",
    "lite3_lidar_v107_standing_visual.stl",
)
REQUIRED_COMPONENTS = (
    "Upper_Mounting_References",
    "Upper_Interface_Enclosure",
    "Laser_Radar_Core",
    "Cooling_Fins",
    "Protective_Hoop",
    "Front_Sensor_Bar",
)
DETERMINISTIC_HASH_OUTPUTS = (
    "lite3_lidar_v107_upper_module.stl",
    "lite3_lidar_v107_standing_visual.stl",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    if not isinstance(result, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return result


def validate_root(root: Path) -> dict[str, Any]:
    report_path = root / "reports" / "validation.json"
    if not report_path.is_file():
        raise FileNotFoundError(report_path)
    report = load_json(report_path)
    if report.get("model_id") != "lite3_lidar_v107_visual_reconstruction":
        raise ValueError("Unexpected model id")
    if report.get("artifact_labels", {}).get("full_assembly") != "visual_only":
        raise ValueError("Full assembly must be labeled visual_only")
    if report.get("artifact_labels", {}).get("forbidden_label") != "fit_validated":
        raise ValueError("Forbidden claim label is missing")
    if abs(float(report["height_error_mm"])) > 1.0:
        raise ValueError("Assembly height misses the 496 mm target")
    if float(report["base_mesh"]["scale"]) != 1.0:
        raise ValueError("Official base mesh scale changed")
    if abs(float(report["assembly_bbox"]["min_mm"][2])) > 1.0e-6:
        raise ValueError("Assembly is not ground aligned")

    component_names = tuple(report.get("required_component_names", []))
    if component_names != REQUIRED_COMPONENTS:
        raise ValueError(
            f"Component contract mismatch: expected {REQUIRED_COMPONENTS}, "
            f"got {component_names}"
        )
    for name in REQUIRED_COMPONENTS:
        component = report["components"].get(name)
        if not component:
            raise ValueError(f"Missing component {name}")
        if not component["valid"] or not component["closed"]:
            raise ValueError(f"Invalid or open component {name}")
        if component["solid_count"] != 1:
            raise ValueError(f"Component {name} is not one solid")

    for filename in REQUIRED_MODELS:
        path = root / "models" / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)
        recorded = report["outputs"].get(filename)
        if not recorded:
            raise ValueError(f"No output record for {filename}")
        if sha256(path) != recorded["sha256"]:
            raise ValueError(f"Output hash mismatch for {filename}")
    if not report["reimport"]["step"]["valid"]:
        raise ValueError("STEP re-import is invalid")
    if report["reimport"]["step"]["solid_count"] < len(REQUIRED_COMPONENTS):
        raise ValueError("STEP re-import lost authored solids")
    if report["reimport"]["upper_stl"]["facet_count"] <= 0:
        raise ValueError("Upper STL is empty")
    if report["reimport"]["standing_visual_stl"]["facet_count"] <= int(
        report["base_mesh"]["facet_count"]
    ):
        raise ValueError("Standing visual STL does not contain authored geometry")
    return report


def compare_reports(
    primary: dict[str, Any],
    second: dict[str, Any],
) -> dict[str, Any]:
    exact_fields = (
        "model_id",
        "required_component_names",
        "object_count",
        "official_target_bbox_mm",
    )
    for field in exact_fields:
        if primary[field] != second[field]:
            raise ValueError(f"Rebuild mismatch in {field}")
    metric_fields = (
        "assembly_bbox",
        "height_error_mm",
        "preserved_width_difference_mm",
        "components",
    )
    for field in metric_fields:
        if primary[field] != second[field]:
            raise ValueError(f"Rebuild geometry-metric mismatch in {field}")

    primary_parameters = Path(primary["parameters_path"])
    second_parameters = Path(second["parameters_path"])
    parameter_hashes = {
        "primary": sha256(primary_parameters),
        "second": sha256(second_parameters),
    }
    parameter_hashes["match"] = (
        parameter_hashes["primary"] == parameter_hashes["second"]
    )
    if not parameter_hashes["match"]:
        raise ValueError("Rebuild parameter values do not match")

    output_hashes = {}
    for filename in REQUIRED_MODELS:
        primary_hash = primary["outputs"][filename]["sha256"]
        second_hash = second["outputs"][filename]["sha256"]
        deterministic_expected = filename in DETERMINISTIC_HASH_OUTPUTS
        hashes_match = primary_hash == second_hash
        if deterministic_expected and not hashes_match:
            raise ValueError(f"Deterministic rebuild hash mismatch for {filename}")
        output_hashes[filename] = {
            "primary": primary_hash,
            "second": second_hash,
            "hashes_match": hashes_match,
            "deterministic_expected": deterministic_expected,
            "note": (
                "Raw hashes must match across clean builds."
                if deterministic_expected
                else "Container/header metadata can differ; geometry metrics are compared."
            ),
        }
    return {
        "parameter_sha256": parameter_hashes,
        "output_hashes": output_hashes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--compare-root", type=Path)
    parser.add_argument("--comparison-report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    primary = validate_root(args.root.resolve())
    if args.compare_root is not None:
        second = validate_root(args.compare_root.resolve())
        reproducibility = compare_reports(primary, second)
        if args.comparison_report is not None:
            comparison_path = args.comparison_report.resolve()
            comparison_path.parent.mkdir(parents=True, exist_ok=True)
            comparison = {
                "schema_version": 1,
                "model_id": primary["model_id"],
                "geometry_metrics_match": True,
                "parameter_values_match": reproducibility["parameter_sha256"][
                    "match"
                ],
                "parameter_sha256": reproducibility["parameter_sha256"],
                "output_hashes": reproducibility["output_hashes"],
                "compared_fields": [
                    "model_id",
                    "required_component_names",
                    "object_count",
                    "official_target_bbox_mm",
                    "assembly_bbox",
                    "height_error_mm",
                    "preserved_width_difference_mm",
                    "components",
                ],
                "primary_validation_sha256": sha256(
                    args.root.resolve() / "reports" / "validation.json"
                ),
                "second_validation_sha256": sha256(
                    args.compare_root.resolve() / "reports" / "validation.json"
                ),
            }
            with comparison_path.open("w", encoding="utf-8") as handle:
                json.dump(comparison, handle, indent=2, sort_keys=True)
                handle.write("\n")
            print(f"comparison_report={comparison_path}")
        print("rebuild_metrics_match=true")
    print("validation_ok=true")
    print(
        "assembly_size_mm="
        + ",".join(
            f"{float(value):.6f}"
            for value in primary["assembly_bbox"]["size_mm"]
        )
    )
    print(f"object_count={primary['object_count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
