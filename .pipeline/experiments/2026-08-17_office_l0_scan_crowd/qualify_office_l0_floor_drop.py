"""Qualify generated Office L0 source-mesh colliders with rigid-body drops."""

from __future__ import annotations

import argparse
import json
import math
import traceback
from pathlib import Path

from isaaclab.app import AppLauncher

from inspect_office_l0_collision import OFFICE_URI
from qualify_office_l0_floor_collision import _bounds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    app = AppLauncher(args).app
    try:
        import numpy as np
        import omni.client
        import isaaclab.sim as sim_utils
        from isaaclab.sim import SimulationCfg, SimulationContext
        from isaacsim.core.api.objects import DynamicSphere
        from isaacsim.core.prims import RigidPrim
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
        rows = []
        for prim in Usd.PrimRange.Stage(sim.stage, Usd.TraverseInstanceProxies()):
            if not prim.IsA(UsdGeom.Mesh):
                continue
            path = str(prim.GetPath())
            if "/SM_Floor_" not in path or "FloorCarpet" in path:
                continue
            bounds = _bounds(cache, prim)
            if bounds is None or abs(0.5 * (bounds[2] + bounds[5])) > 0.02:
                continue
            authored_collision = prim.HasAPI(UsdPhysics.CollisionAPI)
            if not authored_collision:
                UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
                UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(
                    UsdPhysics.Tokens.none
                )
                PhysxSchema.PhysxTriangleMeshCollisionAPI.Apply(prim)
            x0, y0, z0, x1, y1, z1 = bounds
            x = 0.5 * (x0 + x1)
            y = 0.5 * (y0 + y1)
            rows.append(
                {
                    "floor_path": path,
                    "bounds_xyzxyz_m": bounds,
                    "authored_collision_api": authored_collision,
                    "probe_start_m": [x, y, 0.35],
                }
            )
        if not rows:
            raise RuntimeError("no L0 source floor meshes were selected")

        for index, row in enumerate(rows):
            DynamicSphere(
                prim_path=f"/World/FloorProbes/probe_{index:03d}",
                translation=np.asarray(row["probe_start_m"], dtype=np.float64),
                radius=0.05,
                mass=0.05,
                color=np.asarray([0.1, 0.6, 1.0], dtype=np.float32),
            )
        probe_view = RigidPrim("/World/FloorProbes/probe_.*", reset_xform_properties=False)
        sim.reset()
        probe_view.initialize()
        for _ in range(360):
            sim.step(render=False)

        final_positions, _ = probe_view.get_world_poses()
        final_velocities = probe_view.get_velocities()
        if hasattr(final_positions, "detach"):
            final_positions = final_positions.detach().cpu().numpy()
        else:
            final_positions = np.asarray(final_positions)
        if hasattr(final_velocities, "detach"):
            final_velocities = final_velocities.detach().cpu().numpy()
        else:
            final_velocities = np.asarray(final_velocities)
        failures = []
        for index, row in enumerate(rows):
            start = np.asarray(row["probe_start_m"])
            final = final_positions[index]
            velocity = final_velocities[index]
            expected_z = 0.05
            z_error = abs(float(final[2]) - expected_z)
            xy_drift = float(np.linalg.norm(final[:2] - start[:2]))
            speed = float(np.linalg.norm(velocity[:3]))
            passed = z_error <= 0.03 and xy_drift <= 0.05 and speed <= 0.10
            row.update(
                {
                    "probe_final_m": [float(value) for value in final],
                    "probe_final_linear_velocity_mps": [
                        float(value) for value in velocity[:3]
                    ],
                    "z_error_m": z_error,
                    "xy_drift_m": xy_drift,
                    "speed_mps": speed,
                    "qualification_pass": passed,
                }
            )
            if not passed:
                failures.append(row["floor_path"])

        payload = {
            "status": "PASS" if not failures else "FAIL",
            "reviewed": False,
            "office_uri": OFFICE_URI,
            "floor_level": "L0",
            "ground_plane_collision_disabled_for_test": ground.IsValid(),
            "probe_type": "0.05_m_radius_0.05_kg_dynamic_sphere",
            "simulation_steps": 360,
            "simulation_dt_s": 1.0 / 120.0,
            "floor_mesh_count": len(rows),
            "generated_floor_collider_count": sum(
                not row["authored_collision_api"] for row in rows
            ),
            "drop_pass_count": len(rows) - len(failures),
            "drop_failure_count": len(failures),
            "drop_failure_paths": failures,
            "floor_rows": rows,
            "claim_boundary": [
                "source floor visual triangles receive run-stage static triangle-mesh collision",
                "rigid spheres establish tile-centre physical support only",
                "no full-tile sweep, articulated Lite3, route, sensor, pedestrian, or planning claim",
            ],
        }
        args.output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(
            "OFFICE_L0_FLOOR_DROP="
            + json.dumps(
                {
                    key: payload[key]
                    for key in (
                        "status",
                        "floor_mesh_count",
                        "generated_floor_collider_count",
                        "drop_pass_count",
                        "drop_failure_count",
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
