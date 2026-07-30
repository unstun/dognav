#!/usr/bin/env python3
"""Reproduce the rejected J17A-derived Lite3 LiDAR visual candidate.

Dr Sun rejected this track on 2026-07-26 because it imports the Lite3 Venture
FAST-LIVO2 J17A/J20A/S410 parts without evidence that they are the factory
LiDAR V1.0.7 assembly. Running it reproduces negative evidence only.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import trimesh


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
OUTPUT_ROOT = (
    TASK_ROOT / "evidence/official-lidar-v107-visible-replica-candidate"
)
MESH_ROOT = OUTPUT_ROOT / "meshes"
MODEL_ROOT = OUTPUT_ROOT / "models"
MANIFEST = OUTPUT_ROOT / "manifest.json"
MANUAL_POSE_BODY_SOURCE = MODEL_ROOT / "lite3_official_manual_pose.stl"

BASELINE_MODULE_PATH = (
    TASK_ROOT / "research/prepare_official_lidar_v107_baseline.py"
)
DIRECT_MESH_ROOT = TASK_ROOT / "evidence/j17a-direct-camera-candidate/meshes"
DIRECT_MANIFEST = DIRECT_MESH_ROOT.parent / "manifest.json"
DESIGN_DRAWING_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-design-drawings/derived"
)
OFFICIAL_MEDIA_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-26_lite3-current-lidar-official-us-media"
)
RELATED_HARDWARE_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware"
)

# Image registration from the V1.0.7 side render:
# - the factory-visible lower carrier and Interface underside share one datum;
# - the source-extracted upper sensor stack already reaches the published
#   496 mm top height;
# - the related-source J17A lower carrier must therefore sit 18 mm below that
#   upper stack instead of being lifted by invented body-following supports.
UPPER_SENSOR_TRANSLATION_MM = np.asarray([0.0, 0.0, -28.132935])
LOWER_CARRIER_TRANSLATION_MM = np.asarray([0.0, 0.0, -46.132935])

# The Interface is behind the carrier in the official side view.  These values
# are image estimates, not factory dimensions.
INTERFACE_LENGTH_MM = 218.0
INTERFACE_WIDTH_MM = 92.0
INTERFACE_HEIGHT_MM = 44.0
INTERFACE_CENTER_X_MM = -57.0
INTERFACE_BOTTOM_Z_MM = 399.867065
INTERFACE_CORNER_RADIUS_MM = 0.8
INTERFACE_FOOT_RADIUS_MM = 7.5
INTERFACE_FOOT_X_MM = (-135.0, 21.0)
INTERFACE_FOOT_Y_MM = (-36.0, 36.0)
TARGET_GUARD_TOP_MM = 496.0

SENSOR_INPUT_NODES = (
    "MID360_ADAPTER",
    "MID360_GUARD",
    "MID360_BODY",
    "MID360_HOUSING_EXTERIOR",
    "MID360_OPTICAL_WINDOW",
    "MID360_CONNECTOR",
)

COLORS = {
    "FULL_LITE3_OFFICIAL_VISUAL": [210, 214, 220, 255],
    "LITE3_TOP_CONTACT_SURFACE": [205, 209, 214, 255],
    "FACTORY_VISIBLE_LOCAL_CARRIER": [155, 158, 162, 255],
    "MID360_ADAPTER": [151, 154, 158, 255],
    "MID360_GUARD": [36, 38, 42, 255],
    "MID360_BODY": [159, 162, 166, 255],
    "MID360_HOUSING_EXTERIOR": [165, 168, 172, 255],
    "MID360_OPTICAL_WINDOW": [14, 61, 132, 255],
    "MID360_CONNECTOR": [30, 31, 34, 255],
    "D435I_CAMERA": [205, 207, 210, 255],
    "D435_FRONT_FACE_DERIVED": [28, 29, 32, 255],
    "INTERFACE_BODY": [224, 225, 226, 255],
    "INTERFACE_LID": [235, 236, 237, 255],
    "INTERFACE_PORT_POWER": [200, 137, 39, 255],
    "INTERFACE_PORT_DATA": [30, 32, 35, 255],
    "INTERFACE_PORT_USB3": [43, 90, 145, 255],
    "INTERFACE_VENTS": [52, 54, 57, 255],
    "INTERFACE_SERVICE_PANEL": [111, 113, 117, 255],
    "INTERFACE_VISIBLE_FEET": [105, 108, 112, 255],
    "INTERFACE_TOP_FASTENER_HEAD": [70, 72, 75, 255],
    "INTERFACE_SIDE_FASTENER_HEAD": [70, 72, 75, 255],
    "INTERFACE_END_FASTENER_HEADS": [70, 72, 75, 255],
}


def load_base_module():
    spec = importlib.util.spec_from_file_location(
        "official_lidar_v107_baseline_helpers",
        BASELINE_MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load helpers from {BASELINE_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def translated(mesh: trimesh.Trimesh, translation_mm: np.ndarray):
    result = mesh.copy()
    result.apply_translation(translation_mm / 1000.0)
    return result


def make_visible_interface(base, deck_contact_z_mm: float):
    """Create only enclosure features visible in official views."""
    body_height_mm = INTERFACE_HEIGHT_MM - 1.7
    body = base.rounded_rect_prism(
        INTERFACE_LENGTH_MM / 1000.0,
        INTERFACE_WIDTH_MM / 1000.0,
        body_height_mm / 1000.0,
        INTERFACE_CORNER_RADIUS_MM / 1000.0,
        np.asarray(
            [
                INTERFACE_CENTER_X_MM,
                0.0,
                INTERFACE_BOTTOM_Z_MM + body_height_mm / 2.0,
            ]
        )
        / 1000.0,
    )
    front_x_mm = INTERFACE_CENTER_X_MM + INTERFACE_LENGTH_MM / 2.0
    relief = base.box_mm(
        [30.0, 74.0, 7.0],
        [front_x_mm - 13.0, 0.0, INTERFACE_BOTTOM_Z_MM + 3.5],
    )
    body = trimesh.boolean.difference([body, relief], engine="manifold")
    if not isinstance(body, trimesh.Trimesh):
        raise RuntimeError("Visible Interface relief Boolean failed")

    lid = base.rounded_rect_prism(
        (INTERFACE_LENGTH_MM + 2.0) / 1000.0,
        (INTERFACE_WIDTH_MM + 2.0) / 1000.0,
        1.7 / 1000.0,
        3.0 / 1000.0,
        np.asarray(
            [
                INTERFACE_CENTER_X_MM,
                0.0,
                INTERFACE_BOTTOM_Z_MM + INTERFACE_HEIGHT_MM - 0.85,
            ]
        )
        / 1000.0,
    )

    side_y_mm = -INTERFACE_WIDTH_MM / 2.0 - 0.4
    power_ports = base.concatenate(
        [
            base.box_mm(
                [4.4, 0.8, 8.5],
                [
                    INTERFACE_CENTER_X_MM + 57.5 + offset,
                    side_y_mm,
                    INTERFACE_BOTTOM_Z_MM + 22.5,
                ],
            )
            for offset in (-6.0, 0.0, 6.0)
        ]
    )
    data_ports = base.concatenate(
        [
            base.box_mm(
                [11.0, 0.8, 12.0],
                [
                    INTERFACE_CENTER_X_MM + 31.5,
                    side_y_mm,
                    INTERFACE_BOTTOM_Z_MM + 22.5,
                ],
            ),
            base.box_mm(
                [17.0, 0.8, 13.0],
                [
                    INTERFACE_CENTER_X_MM - 52.5,
                    side_y_mm,
                    INTERFACE_BOTTOM_Z_MM + 22.5,
                ],
            ),
            base.box_mm(
                [7.0, 0.8, 14.0],
                [
                    INTERFACE_CENTER_X_MM - 90.5,
                    side_y_mm,
                    INTERFACE_BOTTOM_Z_MM + 22.5,
                ],
            ),
        ]
    )
    usb3 = base.box_mm(
        [8.0, 0.8, 14.0],
        [
            INTERFACE_CENTER_X_MM - 74.5,
            side_y_mm,
            INTERFACE_BOTTOM_Z_MM + 22.5,
        ],
    )
    rear_x_mm = INTERFACE_CENTER_X_MM - INTERFACE_LENGTH_MM / 2.0
    vents = base.concatenate(
        [
            base.box_mm(
                [0.8, 12.0, 2.2],
                [rear_x_mm - 0.4, y_value, z_value],
            )
            for z_value in (
                INTERFACE_BOTTOM_Z_MM + 7.5,
                INTERFACE_BOTTOM_Z_MM + 12.5,
                INTERFACE_BOTTOM_Z_MM + 17.5,
                INTERFACE_BOTTOM_Z_MM + 22.5,
            )
            for y_value in (-24.0, -8.0, 8.0)
        ]
    )
    service_panel = base.box_mm(
        [20.0, 0.8, 19.0],
        [
            INTERFACE_CENTER_X_MM - 60.5,
            INTERFACE_WIDTH_MM / 2.0 + 0.4,
            INTERFACE_BOTTOM_Z_MM + 20.5,
        ],
    )

    foot_height_mm = INTERFACE_BOTTOM_Z_MM - deck_contact_z_mm
    if foot_height_mm <= 0.0:
        raise RuntimeError("Interface visible-foot height is not positive")
    feet = base.concatenate(
        [
            base.cylinder_mm(
                INTERFACE_FOOT_RADIUS_MM,
                foot_height_mm,
                [
                    x_value,
                    y_value,
                    (INTERFACE_BOTTOM_Z_MM + deck_contact_z_mm) / 2.0,
                ],
            )
            for x_value in INTERFACE_FOOT_X_MM
            for y_value in INTERFACE_FOOT_Y_MM
        ]
    )
    top_head = base.cylinder_mm(
        2.6,
        0.7,
        [
            INTERFACE_CENTER_X_MM - 15.5,
            0.0,
            INTERFACE_BOTTOM_Z_MM + INTERFACE_HEIGHT_MM + 0.35,
        ],
    )
    side_head = base.cylinder_mm(
        2.2,
        0.8,
        [
            INTERFACE_CENTER_X_MM + 89.5,
            INTERFACE_WIDTH_MM / 2.0 + 0.4,
            INTERFACE_BOTTOM_Z_MM + 12.0,
        ],
        axis="y",
    )
    end_heads = base.concatenate(
        [
            base.cylinder_mm(
                2.2,
                0.8,
                [
                    rear_x_mm - 0.4,
                    y_value,
                    INTERFACE_BOTTOM_Z_MM + 10.0,
                ],
                axis="x",
            )
            for y_value in (-35.0, 35.0)
        ]
    )
    return {
        "INTERFACE_BODY": body,
        "INTERFACE_LID": lid,
        "INTERFACE_PORT_POWER": power_ports,
        "INTERFACE_PORT_DATA": data_ports,
        "INTERFACE_PORT_USB3": usb3,
        "INTERFACE_VENTS": vents,
        "INTERFACE_SERVICE_PANEL": service_panel,
        "INTERFACE_VISIBLE_FEET": feet,
        "INTERFACE_TOP_FASTENER_HEAD": top_head,
        "INTERFACE_SIDE_FASTENER_HEAD": side_head,
        "INTERFACE_END_FASTENER_HEADS": end_heads,
    }


def main() -> None:
    base = load_base_module()
    MESH_ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    if not MANUAL_POSE_BODY_SOURCE.is_file():
        raise FileNotFoundError(
            "Generate the official manual-pose body in the new evidence "
            f"directory first: {MANUAL_POSE_BODY_SOURCE}"
        )

    full_body = base.load_mm_as_m(MANUAL_POSE_BODY_SOURCE)
    ground_normalization_mm = -float(full_body.bounds[0, 2] * 1000.0)
    full_body.apply_translation(
        np.asarray([0.0, 0.0, ground_normalization_mm]) / 1000.0
    )
    sampler = base.TopSurfaceSampler(full_body)
    interface_contact_samples_mm = [
        sampler.sample_mm(x_value, y_value)
        for x_value in INTERFACE_FOOT_X_MM
        for y_value in INTERFACE_FOOT_Y_MM
    ]
    deck_contact_z_mm = float(np.max(interface_contact_samples_mm))

    meshes: dict[str, trimesh.Trimesh] = {
        "FULL_LITE3_OFFICIAL_VISUAL": full_body,
        "LITE3_TOP_CONTACT_SURFACE": base.derive_top_contact_surface(sampler),
    }
    lower_carrier = base.load_mm_as_m(
        DIRECT_MESH_ROOT / "J17A_SENSOR_CARRIER_SOURCE.stl",
        repair=True,
    )
    meshes["FACTORY_VISIBLE_LOCAL_CARRIER"] = translated(
        lower_carrier,
        LOWER_CARRIER_TRANSLATION_MM,
    )
    for node_name in SENSOR_INPUT_NODES:
        meshes[node_name] = translated(
            base.load_mm_as_m(DIRECT_MESH_ROOT / f"{node_name}.stl"),
            UPPER_SENSOR_TRANSLATION_MM,
        )
    camera = translated(
        base.load_mm_as_m(DIRECT_MESH_ROOT / "D435I_CAMERA_DIRECT.stl"),
        UPPER_SENSOR_TRANSLATION_MM,
    )
    meshes["D435I_CAMERA"] = camera
    meshes["D435_FRONT_FACE_DERIVED"] = (
        base.derive_camera_front_surface(camera)
    )
    meshes.update(make_visible_interface(base, deck_contact_z_mm))

    forbidden_nodes = {
        "J17A_LOCAL_SUPPORTS",
        "J17A_BODY_M3_FASTENERS",
        "J17A_BODY_RECEIVER_PROXIES",
        "J17A_UPWARD_M3_FASTENERS",
        "INTERFACE_M3_FASTENERS",
        "INTERFACE_RECEIVER_PROXIES",
    }
    if forbidden_nodes.intersection(meshes):
        raise RuntimeError("Rejected engineering nodes entered replica scene")

    evidence_classes = {
        "FULL_LITE3_OFFICIAL_VISUAL": "official_visual",
        "LITE3_TOP_CONTACT_SURFACE": "source_derived_visual_surface",
        "FACTORY_VISIBLE_LOCAL_CARRIER": (
            "related_source_geometry_image_registered_to_official_views"
        ),
        "MID360_ADAPTER": "related_source_candidate",
        "MID360_GUARD": "related_source_candidate",
        "MID360_BODY": "official_visual",
        "MID360_HOUSING_EXTERIOR": "official_visual",
        "MID360_OPTICAL_WINDOW": "official_visual",
        "MID360_CONNECTOR": "official_visual",
        "D435I_CAMERA": "official_visual",
        "D435_FRONT_FACE_DERIVED": (
            "source_derived_visual_material_layer"
        ),
        "INTERFACE_BODY": "image_estimate",
        "INTERFACE_LID": "image_estimate",
        "INTERFACE_PORT_POWER": "official_visible_image_estimate",
        "INTERFACE_PORT_DATA": "official_visible_image_estimate",
        "INTERFACE_PORT_USB3": "official_visible_image_estimate",
        "INTERFACE_VENTS": "official_visible_image_estimate",
        "INTERFACE_SERVICE_PANEL": "official_visible_image_estimate",
        "INTERFACE_VISIBLE_FEET": "official_visible_image_estimate",
        "INTERFACE_TOP_FASTENER_HEAD": (
            "official_visible_surface_feature"
        ),
        "INTERFACE_SIDE_FASTENER_HEAD": (
            "official_visible_surface_feature"
        ),
        "INTERFACE_END_FASTENER_HEADS": (
            "official_visible_surface_feature"
        ),
    }
    entries = []
    for name, mesh in meshes.items():
        if mesh.is_empty:
            raise RuntimeError(f"Generated empty mesh: {name}")
        metrics = base.export_mm(mesh, MESH_ROOT / f"{name}.stl")
        entries.append(
            {
                "node_name": name,
                "evidence_class": evidence_classes[name],
                "color_rgba": COLORS[name],
                **metrics,
            }
        )

    guard_top_mm = float(meshes["MID360_GUARD"].bounds[1, 2] * 1000.0)
    carrier_bounds_mm = (
        meshes["FACTORY_VISIBLE_LOCAL_CARRIER"].bounds * 1000.0
    )
    interface_front_x_mm = (
        INTERFACE_CENTER_X_MM + INTERFACE_LENGTH_MM / 2.0
    )
    visible_gap_mm = float(
        carrier_bounds_mm[0, 0] - interface_front_x_mm
    )
    if abs(guard_top_mm - TARGET_GUARD_TOP_MM) > 1.0e-6:
        raise RuntimeError(
            f"Guard top {guard_top_mm:.6f} mm misses published height"
        )
    if visible_gap_mm <= 0.0:
        raise RuntimeError("Interface overlaps the visible local carrier in X")

    source_paths = {
        "official_front_render": (
            DESIGN_DRAWING_ROOT / "lite3-lidar-v107-front-render-original.png"
        ),
        "official_side_render": (
            DESIGN_DRAWING_ROOT / "lite3-lidar-v107-side-render-original.png"
        ),
        "official_front_line_art": (
            DESIGN_DRAWING_ROOT
            / "lite3-lidar-v107-front-line-art-original.png"
        ),
        "official_rear_line_art": (
            DESIGN_DRAWING_ROOT
            / "lite3-lidar-v107-rear-line-art-original.png"
        ),
        "official_current_studio": (
            OFFICIAL_MEDIA_ROOT
            / "source/original/lite3-lidar-current-studio-2048x2048.jpg"
        ),
        "official_current_studio_alt": (
            OFFICIAL_MEDIA_ROOT
            / "source/original/lite3-lidar-current-studio-alt-2048x2048.jpg"
        ),
        "related_j17a_drawing": (
            RELATED_HARDWARE_ROOT / "derived/j17a-drawing.png"
        ),
        "related_j17a_step": (
            RELATED_HARDWARE_ROOT
            / "source/original/1T21-J17A-lidar base.STEP"
        ),
    }
    manifest = {
        "schema_version": 1,
        "purpose": "rejected_j17a_derived_lite3_lidar_visual_evidence",
        "status": "rejected_by_dr_sun_2026_07_26",
        "claim_boundary": (
            "Rejected negative evidence. J17A/J20A/S410 belong to the Lite3 "
            "Venture FAST-LIVO2 extension and do not establish factory LiDAR "
            "V1.0.7 assembly identity, fit, or print readiness."
        ),
        "source_files": {
            name: {
                "path": str(path.resolve()),
                "sha256": base.sha256(path),
            }
            for name, path in source_paths.items()
        },
        "source_extraction_cache": {
            "path": str(DIRECT_MESH_ROOT.resolve()),
            "manifest": str(DIRECT_MANIFEST.resolve()),
            "manifest_sha256": base.sha256(DIRECT_MANIFEST),
        },
        "image_registered_parameters": {
            "upper_sensor_translation_mm": (
                UPPER_SENSOR_TRANSLATION_MM.tolist()
            ),
            "lower_carrier_translation_mm": (
                LOWER_CARRIER_TRANSLATION_MM.tolist()
            ),
            "visible_two_layer_offset_mm": float(
                LOWER_CARRIER_TRANSLATION_MM[2]
                - UPPER_SENSOR_TRANSLATION_MM[2]
            ),
            "interface_envelope_mm": [
                INTERFACE_LENGTH_MM,
                INTERFACE_WIDTH_MM,
                INTERFACE_HEIGHT_MM,
            ],
            "interface_center_x_mm": INTERFACE_CENTER_X_MM,
            "interface_bottom_z_mm": INTERFACE_BOTTOM_Z_MM,
            "interface_visible_foot_axes_mm": [
                [x_value, y_value]
                for x_value in INTERFACE_FOOT_X_MM
                for y_value in INTERFACE_FOOT_Y_MM
            ],
            "deck_contact_z_mm": deck_contact_z_mm,
            "interface_contact_samples_mm": (
                interface_contact_samples_mm
            ),
            "interface_to_carrier_visible_x_gap_mm": visible_gap_mm,
            "guard_top_mm": guard_top_mm,
        },
        "explicitly_absent": sorted(forbidden_nodes)
        + [
            "print_adaptation",
            "spanning_payload_deck",
            "long_external_rails",
            "hidden_factory_receiver_guess",
            "35_mm_clearance_driven_sensor_shift",
        ],
        "entries": entries,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"manifest={MANIFEST}")
    print(f"guard_top_mm={guard_top_mm:.6f}")
    print(f"interface_to_carrier_visible_x_gap_mm={visible_gap_mm:.6f}")
    print(
        "carrier_bounds_mm="
        f"{carrier_bounds_mm.round(6).tolist()}"
    )


if __name__ == "__main__":
    main()
