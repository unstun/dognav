"""Inspect one official USD hierarchy without starting rendering or physics."""

from __future__ import annotations

import argparse
import json
import math
import traceback
from pathlib import Path

from isaaclab.app import AppLauncher

from scene_preview_core import SCENES, candidate_uris


def _bounds(cache, prim):
    aligned = cache.ComputeWorldBound(prim).ComputeAlignedBox()
    values = tuple(float(value) for value in (*aligned.GetMin(), *aligned.GetMax()))
    return values if all(math.isfinite(value) for value in values) else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", choices=sorted(SCENES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=2)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    app = AppLauncher(args).app
    try:
        import omni.client
        import isaaclab.sim as sim_utils
        from isaaclab.sim import SimulationCfg, SimulationContext
        from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
        from pxr import Usd, UsdGeom

        sim = SimulationContext(SimulationCfg(device=args.device))
        attempts = []
        selected_uri = None
        for uri in candidate_uris(ISAAC_NUCLEUS_DIR, args.scene):
            result, entry = omni.client.stat(uri)
            attempts.append({"uri": uri, "result": str(result)})
            if result == omni.client.Result.OK and entry is not None:
                selected_uri = uri
                break
        if selected_uri is None:
            raise RuntimeError(f"no source scene URI resolved: {attempts}")

        cfg = sim_utils.UsdFileCfg(usd_path=selected_uri)
        root = cfg.func("/World/Environment", cfg)
        cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
            useExtentsHint=True,
        )
        rows = []

        def walk(prim, depth):
            imageable = UsdGeom.Imageable(prim)
            visibility = imageable.ComputeVisibility() if imageable else None
            rows.append(
                {
                    "path": str(prim.GetPath()),
                    "type": prim.GetTypeName(),
                    "depth": depth,
                    "child_count": len(list(prim.GetChildren())),
                    "visibility": None if visibility is None else str(visibility),
                    "bounds_xyzxyz_m": _bounds(cache, prim),
                }
            )
            if depth < args.depth:
                for child in prim.GetChildren():
                    walk(child, depth + 1)

        walk(root, 0)
        cameras = []
        xform_cache = UsdGeom.XformCache(Usd.TimeCode.Default())
        for prim in sim.stage.Traverse():
            if not prim.IsA(UsdGeom.Camera):
                continue
            transform = xform_cache.GetLocalToWorldTransform(prim)
            translation = transform.ExtractTranslation()
            cameras.append(
                {
                    "path": str(prim.GetPath()),
                    "position_m": [float(value) for value in translation],
                }
            )

        payload = {
            "status": "source_usd_hierarchy_inspected",
            "reviewed": False,
            "scene": args.scene,
            "selected_uri": selected_uri,
            "uri_attempts": attempts,
            "inspection_depth": args.depth,
            "rows": rows,
            "authored_cameras": cameras,
            "claim_boundary": [
                "USD composition and hierarchy only",
                "no render, physics, collision completeness, sensor, or navigation claim",
            ],
        }
        args.output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[scene-inspect] output={args.output}", flush=True)
        return 0
    except BaseException:
        traceback.print_exc()
        raise
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
