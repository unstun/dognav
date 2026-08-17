"""Build a run-owned USD overlay for the qualified Office L0 floor colliders."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from isaaclab.app import AppLauncher

from inspect_office_l0_collision import OFFICE_URI


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--floor-result", type=Path, required=True)
    parser.add_argument("--retest-result", type=Path, required=True)
    parser.add_argument("--output-usd", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    floor_result = json.loads(args.floor_result.read_text(encoding="utf-8"))
    retest_result = json.loads(args.retest_result.read_text(encoding="utf-8"))
    if retest_result["status"] != "PASS" or retest_result["combined_failure_count"] != 0:
        raise RuntimeError("Office floor collision evidence is not complete")
    args.output_usd.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)

    app = AppLauncher(args).app
    try:
        from pxr import PhysxSchema, Usd, UsdGeom, UsdPhysics

        stage = Usd.Stage.CreateNew(str(args.output_usd.resolve()))
        root = UsdGeom.Xform.Define(stage, "/OfficeL0Physics").GetPrim()
        root.GetReferences().AddReference(OFFICE_URI, "/Root")
        stage.SetDefaultPrim(root)
        overlay_paths = []
        for row in floor_result["floor_rows"]:
            source_path = row["floor_path"]
            relative = source_path.removeprefix("/World/Environment")
            target_path = "/OfficeL0Physics" + relative
            prim = stage.OverridePrim(target_path)
            UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
            UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(
                UsdPhysics.Tokens.none
            )
            PhysxSchema.PhysxTriangleMeshCollisionAPI.Apply(prim)
            overlay_paths.append(target_path)
        ground_path = "/OfficeL0Physics/GroundPlane/CollisionMesh"
        ground = stage.OverridePrim(ground_path)
        UsdPhysics.CollisionAPI.Apply(ground).CreateCollisionEnabledAttr(False)
        city = stage.OverridePrim("/OfficeL0Physics/SM_Buildings")
        UsdGeom.Imageable(city).MakeInvisible()
        stage.GetRootLayer().Save()

        reopened = Usd.Stage.Open(str(args.output_usd.resolve()))
        default_prim = reopened.GetDefaultPrim()
        if not default_prim.IsValid():
            raise RuntimeError("Office physics wrapper has no default prim")
        missing = []
        for path in overlay_paths:
            prim = reopened.GetPrimAtPath(path)
            if not (
                prim.IsValid()
                and prim.HasAPI(UsdPhysics.CollisionAPI)
                and prim.HasAPI(UsdPhysics.MeshCollisionAPI)
                and prim.HasAPI(PhysxSchema.PhysxTriangleMeshCollisionAPI)
            ):
                missing.append(path)
        if missing:
            raise RuntimeError(f"Office wrapper lost collision overlays: {missing[:5]}")
        manifest = {
            "status": "office_l0_physics_wrapper_built",
            "reviewed": False,
            "office_uri": OFFICE_URI,
            "output_usd": str(args.output_usd.resolve()),
            "output_sha256": _sha256(args.output_usd),
            "floor_overlay_count": len(overlay_paths),
            "floor_overlay_paths": overlay_paths,
            "ground_plane_collision_disabled": ground_path,
            "city_context_hidden": "/OfficeL0Physics/SM_Buildings",
            "floor_result": str(args.floor_result.resolve()),
            "floor_result_sha256": _sha256(args.floor_result),
            "retest_result": str(args.retest_result.resolve()),
            "retest_result_sha256": _sha256(args.retest_result),
            "claim_boundary": [
                "USD overlay references official Office source and adds only qualified floor collision schemas",
                "no source NVIDIA asset is copied or modified",
                "no articulated Lite3, route, sensor, pedestrian, or planning claim",
            ],
        }
        args.manifest.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(
            "OFFICE_L0_WRAPPER="
            + json.dumps(
                {
                    "status": manifest["status"],
                    "floor_overlay_count": manifest["floor_overlay_count"],
                    "output_sha256": manifest["output_sha256"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
