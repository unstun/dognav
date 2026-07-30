#!/usr/bin/env python3
"""Validate the evidence-only Lite3 LiDAR V1.0.7 CAD baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
from PIL import Image
import trimesh


TASK_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    TASK_ROOT / "evidence/official-lidar-v107-baseline-candidate"
)
MANIFEST = OUTPUT_ROOT / "manifest.json"
REPORT = OUTPUT_ROOT / "validation_report.json"

REQUIRED_RENDERS = [
    "full-standing-isometric.png",
    "full-standing-front.png",
    "full-standing-side.png",
    "full-standing-rear.png",
    "full-standing-top.png",
    "upper-assembly-isometric.png",
    "upper-assembly-front.png",
    "upper-assembly-side.png",
    "upper-assembly-rear.png",
    "upper-assembly-top.png",
    "assembly-mechanism-isometric.png",
    "assembly-mechanism-side.png",
    "assembly-mechanism-bottom.png",
    "official-vs-candidate-front.png",
    "official-vs-candidate-side.png",
    "official-vs-candidate-isometric.png",
    "official-v107-baseline-comparison.png",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []

    def check(
        name: str,
        passed: bool,
        actual: object,
        expected: object,
    ) -> None:
        checks.append(
            {
                "name": name,
                "passed": bool(passed),
                "actual": actual,
                "expected": expected,
            }
        )

    check(
        "target_identity",
        manifest["target_identity"]
        == "Lite3 LiDAR assembly shown in official V1.0.7 manual",
        manifest["target_identity"],
        "Lite3 LiDAR assembly shown in official V1.0.7 manual",
    )

    entry_names = [entry["node_name"] for entry in manifest["entries"]]
    rejected_names = manifest["excluded_rejected_tracks"]
    rejected_present = sorted(set(entry_names).intersection(rejected_names))
    check(
        "rejected_tracks_absent_from_entries",
        not rejected_present,
        rejected_present,
        [],
    )
    required_nodes = {
        "FULL_LITE3_OFFICIAL_VISUAL",
        "LITE3_TOP_CONTACT_SURFACE",
        "J17A_SENSOR_CARRIER_CANDIDATE",
        "MID360_ADAPTER",
        "MID360_GUARD",
        "MID360_BODY",
        "MID360_HOUSING_EXTERIOR",
        "MID360_OPTICAL_WINDOW",
        "D435I_CAMERA",
        "D435_FRONT_FACE_DERIVED",
        "D435_DIRECT_FASTENER_REFERENCES",
        "INTERFACE_BODY",
        "INTERFACE_LID",
        "INTERFACE_FEET",
        "INTERFACE_M3_FASTENERS",
        "INTERFACE_RECEIVER_PROXIES",
        "J17A_LOCAL_SUPPORTS",
        "J17A_UPWARD_M3_FASTENERS",
        "J17A_BODY_M3_FASTENERS",
        "J17A_BODY_RECEIVER_PROXIES",
    }
    missing_nodes = sorted(required_nodes.difference(entry_names))
    check(
        "required_nodes_present",
        not missing_nodes,
        missing_nodes,
        [],
    )
    evidence_classes = {
        entry["node_name"]: entry["evidence_class"]
        for entry in manifest["entries"]
    }
    expected_classes = {
        "FULL_LITE3_OFFICIAL_VISUAL": "official_visual",
        "LITE3_TOP_CONTACT_SURFACE": (
            "source_derived_visual_surface"
        ),
        "MID360_BODY": "official_visual",
        "MID360_HOUSING_EXTERIOR": "official_visual",
        "MID360_OPTICAL_WINDOW": "official_visual",
        "MID360_CONNECTOR": "official_visual",
        "D435I_CAMERA": "official_visual",
        "J17A_SENSOR_CARRIER_CANDIDATE": (
            "related_source_candidate"
        ),
        "MID360_ADAPTER": "related_source_candidate",
        "MID360_GUARD": "related_source_candidate",
        "D435_FRONT_FACE_DERIVED": (
            "source_derived_visual_material_layer"
        ),
        "D435_DIRECT_FASTENER_REFERENCES": (
            "source_backed_axis_reference"
        ),
        "INTERFACE_BODY": "image_estimate",
        "INTERFACE_LID": "image_estimate",
        "INTERFACE_FEET": "image_estimate",
        "INTERFACE_M3_FASTENERS": (
            "image_inferred_mechanical_proxy"
        ),
        "INTERFACE_RECEIVER_PROXIES": (
            "image_inferred_mechanical_proxy"
        ),
        "J17A_LOCAL_SUPPORTS": (
            "image_inferred_support_geometry"
        ),
        "J17A_UPWARD_M3_FASTENERS": (
            "source_axis_mechanical_proxy"
        ),
        "J17A_BODY_M3_FASTENERS": (
            "image_inferred_mechanical_proxy"
        ),
        "J17A_BODY_RECEIVER_PROXIES": (
            "image_inferred_mechanical_proxy"
        ),
    }
    class_mismatches = {
        name: {
            "actual": evidence_classes.get(name),
            "expected": expected,
        }
        for name, expected in expected_classes.items()
        if evidence_classes.get(name) != expected
    }
    check(
        "evidence_class_partition",
        not class_mismatches,
        class_mismatches,
        {},
    )

    validation = manifest["validation"]
    guard_top_mm = float(validation["guard_top_mm"])
    check(
        "guard_top_matches_official_height",
        abs(guard_top_mm - 496.0) <= 1.0e-6,
        guard_top_mm,
        496.0,
    )
    extents_mm = np.asarray(
        validation["assembled_reference_extents_mm"],
        dtype=float,
    )
    envelope_error_mm = extents_mm - np.asarray([610.0, 370.0, 496.0])
    check(
        "standing_envelope_image_fit",
        abs(float(envelope_error_mm[0])) <= 10.0
        and abs(float(envelope_error_mm[1])) <= 4.0
        and abs(float(envelope_error_mm[2])) <= 1.0e-6,
        {
            "extents_mm": extents_mm.round(6).tolist(),
            "error_mm": envelope_error_mm.round(6).tolist(),
        },
        {
            "target_mm": [610.0, 370.0, 496.0],
            "tolerance_mm": [10.0, 4.0, 1.0e-6],
        },
    )
    interface_overlap = float(
        validation["interface_to_j17a_intersection_mm3"]
    )
    check(
        "interface_carrier_zero_overlap",
        interface_overlap <= 1.0e-6,
        interface_overlap,
        "<= 0.000001 mm3",
    )
    interface_support_overlap = float(
        validation["interface_to_local_support_intersection_mm3"]
    )
    check(
        "interface_local_support_zero_overlap",
        interface_support_overlap <= 1.0e-6,
        interface_support_overlap,
        "<= 0.000001 mm3",
    )
    support_body_clearance = float(
        validation[
            "sampled_local_support_to_body_minimum_clearance_mm"
        ]
    )
    check(
        "profiled_supports_do_not_penetrate_body",
        0.0 <= support_body_clearance <= 0.5,
        {
            "minimum_clearance_mm": support_body_clearance,
            "sample_count": validation[
                "sampled_local_support_to_body_sample_count"
            ],
        },
        {
            "minimum_clearance_mm": [0.0, 0.5],
            "sample_count": "> 0",
        },
    )
    unintended_mount_overlap = float(
        validation["unintended_mount_overlap_mm3"]
    )
    check(
        "mounting_chains_have_no_unintended_overlap",
        unintended_mount_overlap <= 1.0e-6,
        {
            "total_mm3": unintended_mount_overlap,
            "breakdown_mm3": validation[
                "unintended_mount_overlap_breakdown_mm3"
            ],
        },
        "<= 0.000001 mm3",
    )
    image_parameters = manifest["image_estimated_parameters"]
    mounting_pad_height_mm = float(
        image_parameters["interface_mounting_pad_height_mm"]
    )
    interface_bottom_z_mm = float(
        image_parameters["interface_bottom_z_mm"]
    )
    deck_contact_z_mm = float(
        image_parameters["interface_deck_contact_z_mm"]
    )
    check(
        "interface_mounting_pads_bridge_deck_gap",
        mounting_pad_height_mm > 0.0
        and abs(
            mounting_pad_height_mm
            - (interface_bottom_z_mm - deck_contact_z_mm)
        )
        <= 1.0e-6,
        {
            "pad_height_mm": mounting_pad_height_mm,
            "interface_bottom_z_mm": interface_bottom_z_mm,
            "deck_contact_z_mm": deck_contact_z_mm,
        },
        "positive pad height exactly spanning image-registered deck gap",
    )
    interface_chain = image_parameters["interface_mounting_chain"]
    check(
        "interface_four_fastened_feet",
        len(interface_chain["foot_axes_mm"]) == 4
        and float(interface_chain["clearance_hole_diameter_mm"])
        > float(interface_chain["receiver_minor_diameter_mm"])
        and float(interface_chain["receiver_depth_mm"]) > 0.0,
        interface_chain,
        "four bored feet with M3 fastener and receiver proxies",
    )
    j17a_chain = image_parameters["j17a_mounting_chain"]
    support_records = j17a_chain["support_records"]
    check(
        "j17a_four_m3_local_supports",
        j17a_chain["source_thread_callout"] == "4 x M3"
        and j17a_chain["source_pattern_mm"] == [110.0, 86.0]
        and len(j17a_chain["current_axes_mm"]) == 4
        and len(support_records) == 4
        and all(
            float(record["j17a_seating_z_mm"])
            > float(record["main_body_surface_z_mm"])
            for record in support_records
        ),
        j17a_chain,
        "four source-axis M3 supports with separate body fastener axes",
    )
    camera_contact = float(
        validation["d435_to_j17a_sampled_minimum_distance_mm"]
    )
    check(
        "d435_direct_mount_contact",
        camera_contact <= 0.01,
        camera_contact,
        "<= 0.01 mm sampled surface distance",
    )

    pose = manifest["image_estimated_parameters"]["manual_pose"]
    check(
        "manual_pose_parameters",
        abs(float(pose["hip_y_rad"]) + 0.68) <= 1.0e-9
        and abs(float(pose["knee_rad"]) - 1.48) <= 1.0e-9,
        pose,
        {
            "hip_y_rad": -0.68,
            "knee_rad": 1.48,
            "classification": "image_estimate_from_manual_side_view",
        },
    )

    for source_name, source in manifest["source_files"].items():
        if "sha256" not in source:
            continue
        path = Path(source["path"])
        actual_hash = sha256(path) if path.is_file() else None
        check(
            f"source_hash.{source_name}",
            actual_hash == source["sha256"],
            actual_hash,
            source["sha256"],
        )

    interface_path = Path(manifest["models"]["interface_stl"])
    interface = trimesh.load_mesh(
        interface_path,
        process=True,
        validate=True,
    )
    interface_components = len(
        interface.split(only_watertight=False)
    )
    check(
        "interface_reference_stl",
        interface.is_watertight
        and interface.is_winding_consistent
        and interface_components == 2,
        {
            "watertight": bool(interface.is_watertight),
            "winding_consistent": bool(interface.is_winding_consistent),
            "connected_components": interface_components,
        },
        {
            "watertight": True,
            "winding_consistent": True,
            "connected_components": 2,
        },
    )

    fcstd_path = Path(manifest["models"]["assembled_fcstd"])
    fcstd_ok = (
        fcstd_path.is_file()
        and fcstd_path.stat().st_size > 0
        and zipfile.is_zipfile(fcstd_path)
    )
    bad_zip_member = None
    document_xml = b""
    if fcstd_ok:
        with zipfile.ZipFile(fcstd_path) as archive:
            bad_zip_member = archive.testzip()
            document_xml = archive.read("Document.xml")
    check(
        "freecad_model_readable",
        fcstd_ok and bad_zip_member is None,
        {
            "path": str(fcstd_path),
            "size_bytes": (
                fcstd_path.stat().st_size if fcstd_path.is_file() else None
            ),
            "bad_zip_member": bad_zip_member,
        },
        "readable non-empty FCStd archive",
    )
    rejected_fcstd = [
        name
        for name in rejected_names
        if name.encode("utf-8") in document_xml
    ]
    check(
        "rejected_tracks_absent_from_fcstd",
        not rejected_fcstd,
        rejected_fcstd,
        [],
    )
    required_mechanical_fcstd_nodes = {
        "INTERFACE_M3_FASTENERS",
        "INTERFACE_RECEIVER_PROXIES",
        "J17A_LOCAL_SUPPORTS",
        "J17A_UPWARD_M3_FASTENERS",
        "J17A_BODY_M3_FASTENERS",
        "J17A_BODY_RECEIVER_PROXIES",
    }
    missing_mechanical_fcstd_nodes = sorted(
        name
        for name in required_mechanical_fcstd_nodes
        if name.encode("utf-8") not in document_xml
    )
    check(
        "mechanical_chain_present_in_fcstd",
        not missing_mechanical_fcstd_nodes,
        missing_mechanical_fcstd_nodes,
        [],
    )

    render_metrics: dict[str, object] = {}
    renders_ok = True
    for name in REQUIRED_RENDERS:
        path = OUTPUT_ROOT / name
        if not path.is_file() or path.stat().st_size == 0:
            render_metrics[name] = None
            renders_ok = False
            continue
        with Image.open(path) as image:
            render_metrics[name] = {
                "size_px": list(image.size),
                "size_bytes": path.stat().st_size,
            }
            if image.width < 1000 or image.height < 900:
                renders_ok = False
    check(
        "review_renders_complete",
        renders_ok,
        render_metrics,
        {
            "count": len(REQUIRED_RENDERS),
            "minimum_size_px": [1000, 900],
        },
    )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "schema_version": 1,
        "candidate": str(OUTPUT_ROOT.resolve()),
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "status": "passed" if not failed else "failed",
        "checks": checks,
    }
    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"report={REPORT}")
    print(
        f"checks={report['passed_count']}/{report['check_count']}"
    )
    print(f"status={report['status']}")
    if failed:
        for item in failed:
            print(
                f"FAILED {item['name']}: "
                f"actual={item['actual']!r} "
                f"expected={item['expected']!r}"
            )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
