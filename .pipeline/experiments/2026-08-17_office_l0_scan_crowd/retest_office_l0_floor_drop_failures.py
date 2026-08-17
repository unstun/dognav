"""Retest failed Office floor-centre drops at four inset source-mesh points."""

from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

from isaaclab.app import AppLauncher

from inspect_office_l0_collision import OFFICE_URI
from qualify_office_l0_floor_drop import _bounds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if not args.prior_result.is_file():
        raise FileNotFoundError(args.prior_result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prior = json.loads(args.prior_result.read_text(encoding="utf-8"))
    failed_paths = set(prior["drop_failure_paths"])
    if not failed_paths:
        raise RuntimeError("prior result has no failed paths to retest")

    app = AppLauncher(args).app
    try:
        import numpy as np
        import isaaclab.sim as sim_utils
        from isaaclab.sim import SimulationCfg, SimulationContext
        from isaacsim.core.api.objects import DynamicSphere
        from isaacsim.core.prims import RigidPrim
        from pxr import PhysxSchema, Usd, UsdGeom, UsdPhysics

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
        selected = {}
        for prim in Usd.PrimRange.Stage(sim.stage, Usd.TraverseInstanceProxies()):
            if not prim.IsA(UsdGeom.Mesh):
                continue
            path = str(prim.GetPath())
            bounds = _bounds(cache, prim)
            if bounds is None:
                continue
            if "/SM_Floor_" in path and "FloorCarpet" not in path:
                center_z = 0.5 * (bounds[2] + bounds[5])
                if abs(center_z) <= 0.02 and not prim.HasAPI(UsdPhysics.CollisionAPI):
                    UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
                    UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(
                        UsdPhysics.Tokens.none
                    )
                    PhysxSchema.PhysxTriangleMeshCollisionAPI.Apply(prim)
            if path in failed_paths:
                selected[path] = bounds
        if set(selected) != failed_paths:
            raise RuntimeError(
                f"failed floor paths were not all found: {sorted(failed_paths - set(selected))}"
            )

        probes = []
        fractions = ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75))
        for floor_index, (path, bounds) in enumerate(sorted(selected.items())):
            x0, y0, _, x1, y1, _ = bounds
            for sample_index, (fx, fy) in enumerate(fractions):
                start = [x0 + fx * (x1 - x0), y0 + fy * (y1 - y0), 0.35]
                DynamicSphere(
                    prim_path=f"/World/RetestProbes/probe_{floor_index:02d}_{sample_index:02d}",
                    translation=np.asarray(start, dtype=np.float64),
                    radius=0.05,
                    mass=0.05,
                    color=np.asarray([1.0, 0.4, 0.1], dtype=np.float32),
                )
                probes.append({"floor_path": path, "start_m": start})

        view = RigidPrim("/World/RetestProbes/probe_.*", reset_xform_properties=False)
        sim.reset()
        view.initialize()
        for _ in range(480):
            sim.step(render=False)
        positions, _ = view.get_world_poses()
        velocities = view.get_velocities()
        positions = positions.detach().cpu().numpy()
        velocities = velocities.detach().cpu().numpy()

        floor_pass = {path: False for path in failed_paths}
        for index, probe in enumerate(probes):
            start = np.asarray(probe["start_m"])
            final = positions[index]
            velocity = velocities[index]
            z_error = abs(float(final[2]) - 0.05)
            xy_drift = float(np.linalg.norm(final[:2] - start[:2]))
            speed = float(np.linalg.norm(velocity[:3]))
            passed = z_error <= 0.03 and xy_drift <= 0.05 and speed <= 0.10
            probe.update(
                {
                    "final_m": [float(value) for value in final],
                    "z_error_m": z_error,
                    "xy_drift_m": xy_drift,
                    "speed_mps": speed,
                    "qualification_pass": passed,
                }
            )
            floor_pass[probe["floor_path"]] |= passed

        combined_pass_count = int(prior["drop_pass_count"]) + sum(floor_pass.values())
        payload = {
            "status": "PASS" if all(floor_pass.values()) else "FAIL",
            "reviewed": False,
            "prior_result": str(args.prior_result),
            "prior_drop_pass_count": prior["drop_pass_count"],
            "retested_floor_count": len(floor_pass),
            "retested_floor_pass": floor_pass,
            "combined_floor_count": prior["floor_mesh_count"],
            "combined_pass_count": combined_pass_count,
            "combined_failure_count": prior["floor_mesh_count"] - combined_pass_count,
            "samples": probes,
            "claim_boundary": [
                "four inset rigid-sphere drops retest only prior centre-probe failures",
                "combined result establishes one stable support point per source L0 floor tile",
                "no full-tile sweep, articulated Lite3, route, sensor, pedestrian, or planning claim",
            ],
        }
        args.output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(
            "OFFICE_L0_FLOOR_RETEST="
            + json.dumps(
                {
                    key: payload[key]
                    for key in (
                        "status",
                        "retested_floor_pass",
                        "combined_pass_count",
                        "combined_failure_count",
                    )
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return 0 if payload["status"] == "PASS" else 2
    except BaseException:
        traceback.print_exc()
        raise
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
