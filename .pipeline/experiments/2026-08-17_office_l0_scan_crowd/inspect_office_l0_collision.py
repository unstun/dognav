"""Inventory source-mesh collision coverage for the official Office L0."""

from __future__ import annotations

import argparse
import json
import math
import traceback
from collections import Counter
from pathlib import Path

from isaaclab.app import AppLauncher


OFFICE_URI = (
    "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/"
    "Isaac/5.1/Isaac/Environments/Office/office.usd"
)
L0_Z_MIN = -0.15
L0_Z_MAX = 3.15
EXCLUDED_CONTEXT = "/World/Environment/SM_Buildings"
ROUTE_CATEGORIES = (
    "Floor",
    "Wall",
    "Door",
    "Desk",
    "Table",
    "Chair",
    "Reception",
    "Stairs",
    "Elevator",
)


def _bounds(cache, prim):
    aligned = cache.ComputeWorldBound(prim).ComputeAlignedBox()
    values = tuple(float(value) for value in (*aligned.GetMin(), *aligned.GetMax()))
    if not all(math.isfinite(value) for value in values):
        return None
    x0, y0, z0, x1, y1, z1 = values
    if x1 < x0 or y1 < y0 or z1 < z0 or max(abs(value) for value in values) > 1000.0:
        return None
    return values


def _category(path: str) -> str:
    for category in ROUTE_CATEGORIES:
        if category.lower() in path.lower():
            return category
    return "Other"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    app = AppLauncher(args).app
    try:
        import omni.client
        import isaaclab.sim as sim_utils
        from isaaclab.sim import SimulationCfg, SimulationContext
        from pxr import Usd, UsdGeom, UsdPhysics

        result, entry = omni.client.stat(OFFICE_URI)
        if result != omni.client.Result.OK or entry is None:
            raise RuntimeError(f"Office URI did not resolve: {result}")
        sim = SimulationContext(SimulationCfg(device=args.device))
        cfg = sim_utils.UsdFileCfg(usd_path=OFFICE_URI)
        cfg.func("/World/Environment", cfg)
        for _ in range(20):
            app.update()

        cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
            useExtentsHint=True,
        )
        rows = []
        category_counts = Counter()
        category_collision_counts = Counter()
        prim_range = Usd.PrimRange.Stage(sim.stage, Usd.TraverseInstanceProxies())
        for prim in prim_range:
            path = str(prim.GetPath())
            if path == EXCLUDED_CONTEXT or path.startswith(EXCLUDED_CONTEXT + "/"):
                continue
            if not prim.IsA(UsdGeom.Mesh):
                continue
            bounds = _bounds(cache, prim)
            if bounds is None or bounds[5] < L0_Z_MIN or bounds[2] > L0_Z_MAX:
                continue
            collision = prim.HasAPI(UsdPhysics.CollisionAPI)
            mesh_collision = prim.HasAPI(UsdPhysics.MeshCollisionAPI)
            category = _category(path)
            category_counts[category] += 1
            if collision:
                category_collision_counts[category] += 1
            mesh = UsdGeom.Mesh(prim)
            points = mesh.GetPointsAttr().Get()
            faces = mesh.GetFaceVertexCountsAttr().Get()
            rows.append(
                {
                    "path": path,
                    "category": category,
                    "bounds_xyzxyz_m": bounds,
                    "point_count": 0 if points is None else len(points),
                    "face_count": 0 if faces is None else len(faces),
                    "collision_api": collision,
                    "mesh_collision_api": mesh_collision,
                    "instance": prim.IsInstance(),
                    "instance_proxy": prim.IsInstanceProxy(),
                    "in_prototype": prim.IsInPrototype(),
                    "active": prim.IsActive(),
                    "loaded": prim.IsLoaded(),
                }
            )

        rows.sort(key=lambda row: row["path"])
        uncovered = [row for row in rows if not row["collision_api"]]
        payload = {
            "status": "office_l0_source_collision_inventory_complete",
            "reviewed": False,
            "office_uri": OFFICE_URI,
            "excluded_context": EXCLUDED_CONTEXT,
            "l0_z_interval_m": [L0_Z_MIN, L0_Z_MAX],
            "mesh_count": len(rows),
            "collision_mesh_count": len(rows) - len(uncovered),
            "uncovered_mesh_count": len(uncovered),
            "category_mesh_counts": dict(sorted(category_counts.items())),
            "category_collision_counts": dict(sorted(category_collision_counts.items())),
            "instance_proxy_count": sum(row["instance_proxy"] for row in rows),
            "prototype_mesh_count": sum(row["in_prototype"] for row in rows),
            "route_relevant_uncovered_count": sum(
                row["category"] != "Other" for row in uncovered
            ),
            "rows": rows,
            "claim_boundary": [
                "read-only source-mesh and authored CollisionAPI inventory",
                "no collider generation, physics, support, sensor, route, or planning claim",
            ],
        }
        args.output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(
            "OFFICE_L0_COLLISION_INVENTORY="
            + json.dumps(
                {
                    key: payload[key]
                    for key in (
                        "mesh_count",
                        "collision_mesh_count",
                        "uncovered_mesh_count",
                        "instance_proxy_count",
                        "prototype_mesh_count",
                        "route_relevant_uncovered_count",
                        "category_mesh_counts",
                        "category_collision_counts",
                    )
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return 0
    except BaseException:
        traceback.print_exc()
        raise
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
