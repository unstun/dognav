"""Create and ray-qualify source-mesh colliders for official Office L0 floors."""

from __future__ import annotations

import argparse
import json
import math
import traceback
from pathlib import Path

from isaaclab.app import AppLauncher

from inspect_office_l0_collision import OFFICE_URI


def _bounds(cache, prim):
    aligned = cache.ComputeWorldBound(prim).ComputeAlignedBox()
    values = tuple(float(value) for value in (*aligned.GetMin(), *aligned.GetMax()))
    if not all(math.isfinite(value) for value in values):
        return None
    x0, y0, z0, x1, y1, z1 = values
    if x1 < x0 or y1 < y0 or z1 < z0 or max(abs(value) for value in values) > 1000.0:
        return None
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    app = AppLauncher(args).app
    try:
        import carb
        import omni.client
        import isaaclab.sim as sim_utils
        from isaaclab.sim import SimulationCfg, SimulationContext
        from omni.physx import get_physx_scene_query_interface
        from pxr import PhysxSchema, Usd, UsdGeom, UsdPhysics

        result, entry = omni.client.stat(OFFICE_URI)
        if result != omni.client.Result.OK or entry is None:
            raise RuntimeError(f"Office URI did not resolve: {result}")
        sim = SimulationContext(SimulationCfg(device=args.device, dt=1.0 / 120.0))
        cfg = sim_utils.UsdFileCfg(usd_path=OFFICE_URI)
        cfg.func("/World/Environment", cfg)
        for _ in range(20):
            app.update()

        ground = sim.stage.GetPrimAtPath("/World/Environment/GroundPlane/CollisionMesh")
        if ground.IsValid() and ground.HasAPI(UsdPhysics.CollisionAPI):
            UsdPhysics.CollisionAPI(ground).GetCollisionEnabledAttr().Set(False)

        cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
            useExtentsHint=True,
        )
        floor_rows = []
        prim_range = Usd.PrimRange.Stage(sim.stage, Usd.TraverseInstanceProxies())
        for prim in prim_range:
            if not prim.IsA(UsdGeom.Mesh):
                continue
            path = str(prim.GetPath())
            if "/SM_Floor_" not in path or "FloorCarpet" in path:
                continue
            bounds = _bounds(cache, prim)
            if bounds is None:
                continue
            center_z = 0.5 * (bounds[2] + bounds[5])
            if abs(center_z) > 0.02:
                continue
            authored_collision = prim.HasAPI(UsdPhysics.CollisionAPI)
            if not authored_collision:
                UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
                UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(
                    UsdPhysics.Tokens.none
                )
                PhysxSchema.PhysxTriangleMeshCollisionAPI.Apply(prim)
            floor_rows.append(
                {
                    "path": path,
                    "bounds_xyzxyz_m": bounds,
                    "authored_collision_api": authored_collision,
                    "generated_collision_api": not authored_collision,
                    "approximation": "none_static_triangle_mesh",
                }
            )
        if not floor_rows:
            raise RuntimeError("no L0 source floor meshes were selected")

        import omni.physx

        omni.physx.acquire_physx_interface().force_load_physics_from_usd()
        sim.reset()
        for _ in range(12):
            sim.step(render=False)
        query = get_physx_scene_query_interface()
        failures = []
        for row in floor_rows:
            x0, y0, z0, x1, y1, z1 = row["bounds_xyzxyz_m"]
            x = 0.5 * (x0 + x1)
            y = 0.5 * (y0 + y1)
            origin = carb.Float3(x, y, 0.25)
            direction = carb.Float3(0.0, 0.0, -1.0)
            hit = query.raycast_closest(origin, direction, 0.75, True)
            record = {
                "origin_m": [x, y, 0.25],
                "hit": bool(hit.get("hit", False)),
                "collision": str(hit.get("collision", "")),
                "distance_m": float(hit.get("distance", math.nan)),
                "position_m": [float(value) for value in hit.get("position", ())],
                "normal": [float(value) for value in hit.get("normal", ())],
            }
            row["centre_downward_raycast"] = record
            expected_prefix = row["path"]
            hit_source_floor = record["hit"] and record["collision"] == expected_prefix
            position_ok = (
                len(record["position_m"]) == 3
                and abs(record["position_m"][2] - 0.5 * (z0 + z1)) <= 0.03
            )
            normal_ok = len(record["normal"]) == 3 and record["normal"][2] >= 0.9
            row["qualification_pass"] = hit_source_floor and position_ok and normal_ok
            if not row["qualification_pass"]:
                failures.append(row["path"])

        payload = {
            "status": "PASS" if not failures else "FAIL",
            "reviewed": False,
            "office_uri": OFFICE_URI,
            "floor_level": "L0",
            "floor_z_m": 0.0,
            "ground_plane_collision_disabled_for_test": ground.IsValid(),
            "floor_mesh_count": len(floor_rows),
            "generated_floor_collider_count": sum(
                row["generated_collision_api"] for row in floor_rows
            ),
            "authored_floor_collider_count": sum(
                row["authored_collision_api"] for row in floor_rows
            ),
            "raycast_pass_count": len(floor_rows) - len(failures),
            "raycast_failure_count": len(failures),
            "raycast_failure_paths": failures,
            "floor_rows": floor_rows,
            "claim_boundary": [
                "source floor visual triangles receive run-stage static triangle-mesh CollisionAPI",
                "centre-point downward raycasts qualify floor support coverage only",
                "no articulated Lite3 support, route-wide sweep, sensor, pedestrian, or planning claim",
            ],
        }
        args.output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(
            "OFFICE_L0_FLOOR_COLLISION="
            + json.dumps(
                {
                    key: payload[key]
                    for key in (
                        "status",
                        "floor_mesh_count",
                        "generated_floor_collider_count",
                        "authored_floor_collider_count",
                        "raycast_pass_count",
                        "raycast_failure_count",
                    )
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return 0 if not failures else 2
    except BaseException:
        traceback.print_exc()
        raise
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
