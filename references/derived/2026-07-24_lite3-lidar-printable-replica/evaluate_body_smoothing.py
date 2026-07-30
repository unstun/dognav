#!/usr/bin/env python3
"""Evaluate a topology-preserving smoothing candidate for Lite3 print masters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import manifold3d as md
import numpy as np
import trimesh
from trimesh import smoothing

import build_printable_replica as build


ROOT = Path(__file__).resolve().parent
COMPONENTS = ("torso", "hip", "thigh", "shank")


def component_metrics(
    before: trimesh.Trimesh,
    after: trimesh.Trimesh,
) -> dict[str, Any]:
    displacement = np.linalg.norm(after.vertices - before.vertices, axis=1)
    before_volume = abs(float(before.volume))
    after_volume = abs(float(after.volume))
    manifold = build.mesh_to_manifold(after)
    return {
        "vertices": int(len(after.vertices)),
        "faces": int(len(after.faces)),
        "watertight": bool(after.is_watertight),
        "winding_consistent": bool(after.is_winding_consistent),
        "manifold_status": str(manifold.status()),
        "connected_components": int(
            len(after.split(only_watertight=True))
        ),
        "bbox_size_before_mm": before.extents.tolist(),
        "bbox_size_after_mm": after.extents.tolist(),
        "volume_before_mm3": before_volume,
        "volume_after_mm3": after_volume,
        "volume_change_percent": (
            (after_volume - before_volume) / before_volume * 100.0
        ),
        "vertex_displacement_mm": {
            "median": float(np.median(displacement)),
            "p95": float(np.quantile(displacement, 0.95)),
            "p99": float(np.quantile(displacement, 0.99)),
            "max": float(np.max(displacement)),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--lambda-value", type=float, default=0.4)
    parser.add_argument("--nu", type=float, default=0.41)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = (
        ROOT
        / "evidence"
        / "body-diagnostic"
        / f"smoothed-candidate-{args.iterations:02d}"
    )
    report_path = output / "smoothing-report.json"
    output.mkdir(parents=True, exist_ok=True)
    config = build.load_parameters()
    masters_m: dict[str, trimesh.Trimesh] = {}
    report: dict[str, Any] = {
        "schema_version": 1,
        "method": {
            "name": "trimesh.filter_taubin",
            "lambda": args.lambda_value,
            "nu": args.nu,
            "iterations": args.iterations,
            "topology_preserving": True,
        },
        "components": {},
    }
    for name in COMPONENTS:
        path = ROOT / "models" / "master_1_1" / f"{name}_master_1_1.stl"
        before = trimesh.load_mesh(path, process=True, validate=True)
        before.remove_unreferenced_vertices()
        after = before.copy()
        smoothing.filter_taubin(
            after,
            lamb=args.lambda_value,
            nu=args.nu,
            iterations=args.iterations,
        )
        after.remove_unreferenced_vertices()
        metrics = component_metrics(before, after)
        if not (
            metrics["watertight"]
            and metrics["winding_consistent"]
            and metrics["manifold_status"] == str(md.Error.NoError)
            and metrics["connected_components"] == 1
        ):
            raise ValueError(f"Smoothing invalidated {name}: {metrics}")
        output_path = output / f"{name}_smoothed_master_1_1.stl"
        build.write_stl(output_path, after)
        master_m = after.copy()
        master_m.apply_scale(0.001)
        masters_m[name] = master_m
        report["components"][name] = metrics
        print(
            f"candidate={name} "
            f"p99_displacement_mm="
            f"{metrics['vertex_displacement_mm']['p99']:.6f} "
            f"volume_change_percent={metrics['volume_change_percent']:.6f}",
            flush=True,
        )

    repo_root = build.find_repo_root(ROOT)
    sources = build.resolve_sources(config, repo_root)
    pose = config["factory_standing_pose"]
    robot, transforms, _ = build.resolve_urdf_transforms(
        sources["urdf"],
        float(pose["hip_y_rad"]["value"]),
        float(pose["knee_rad"]["value"]),
        float(pose["foot_collision_radius_mm"]["value"]) / 1000.0,
    )
    world = build.build_world_links(robot, transforms, masters_m)
    base_min_z = min(mesh.bounds[0, 2] for mesh in world.values())
    world = {
        name: build.shifted_mesh(mesh, np.asarray([0.0, 0.0, -base_min_z]))
        for name, mesh in world.items()
    }
    build.export_scene(
        world,
        output / "lite3-smoothed-body-candidate.glb",
        millimetres=False,
    )
    assembled_mm = trimesh.util.concatenate(list(world.values()))
    assembled_mm.apply_scale(1000.0)
    assembled_mm.export(
        output / "lite3-smoothed-body-candidate.stl",
        file_type="stl",
    )
    report["assembled_bbox_mm"] = (
        (assembled_mm.bounds[1] - assembled_mm.bounds[0]).tolist()
    )
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"report={report_path}", flush=True)


if __name__ == "__main__":
    main()
