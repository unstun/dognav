"""Load and capture one official Isaac Sim scene on the 5070 Ti.

This is a visual and stage-inventory preflight. Optional Lite3 URDF insertion
uses a fixed base only as a scale reference and is not locomotion evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import traceback
from pathlib import Path

from isaaclab.app import AppLauncher

from scene_preview_core import SCENES, candidate_uris, scene_views


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _world_bounds(prim):
    from pxr import Gf, Usd, UsdGeom

    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
        useExtentsHint=True,
    )
    aligned = cache.ComputeWorldBound(prim).ComputeAlignedBox()
    lower = aligned.GetMin()
    upper = aligned.GetMax()
    values = tuple(float(value) for value in (*lower, *upper))
    if not all(math.isfinite(value) for value in values):
        raise RuntimeError(f"scene produced non-finite bounds: {values}")
    return values


def _capture_replicator(
    app,
    output: Path,
    width: int,
    height: int,
    *,
    eye=None,
    target=None,
    camera_prim: str | None = None,
    settle_frames: int = 24,
) -> None:
    import imageio.v3 as imageio
    import numpy as np
    import omni.replicator.core as rep

    if camera_prim is None:
        if eye is None or target is None:
            raise ValueError("eye and target are required without camera_prim")
        camera = rep.create.camera(position=eye, look_at=target)
    else:
        camera = camera_prim
    render_product = rep.create.render_product(camera, (width, height))
    annotator = rep.AnnotatorRegistry.get_annotator("rgb", device="cpu")
    annotator.attach(render_product)
    data = None
    for _ in range(240):
        app.update()
        candidate = annotator.get_data()
        if getattr(candidate, "size", 0) >= width * height * 3:
            data = candidate
            break
    if data is None:
        raise RuntimeError("Replicator RGB annotator produced no frame")
    for _ in range(settle_frames):
        app.update()
    latest = annotator.get_data()
    if getattr(latest, "size", 0) >= width * height * 3:
        data = latest
    array = np.asarray(data)
    if array.ndim != 3 or array.shape[2] < 3:
        raise RuntimeError(f"unexpected RGB frame shape: {array.shape}")
    array = array[..., :3]
    if array.dtype != np.uint8:
        maximum = float(np.nanmax(array)) if array.size else 0.0
        scale = 255.0 if maximum <= 1.0 else 1.0
        array = np.clip(array * scale, 0.0, 255.0).astype(np.uint8)
    imageio.imwrite(output, array)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"camera did not create {output}")
    annotator.detach(render_product)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", choices=sorted(SCENES), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--robot-asset", type=Path)
    parser.add_argument("--robot-position", type=float, nargs=3)
    parser.add_argument(
        "--clay",
        action="store_true",
        help="override source materials for a geometry-only performance preview",
    )
    parser.add_argument("--hide-prim", action="append", default=[])
    parser.add_argument("--authored-camera-limit", type=int, default=0)
    parser.add_argument("--camera-eye", type=float, nargs=3, action="append")
    parser.add_argument("--camera-target", type=float, nargs=3, action="append")
    parser.add_argument("--crop-center", type=float, nargs=2)
    parser.add_argument("--crop-radius", type=float)
    parser.add_argument(
        "--subset-reference",
        action="store_true",
        help="compose only selected direct children from the official source USD",
    )
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--settle-frames", type=int, default=24)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()

    if args.robot_asset is not None and not args.robot_asset.is_file():
        raise FileNotFoundError(args.robot_asset)
    if args.robot_asset is not None and args.robot_position is None:
        raise ValueError("--robot-position is required with --robot-asset")
    if args.width < 640 or args.height < 360:
        raise ValueError("preview resolution must be at least 640x360")
    if args.settle_frames < 0 or args.settle_frames > 240:
        raise ValueError("--settle-frames must be within [0, 240]")
    if (args.crop_center is None) != (args.crop_radius is None):
        raise ValueError("--crop-center and --crop-radius must be used together")
    if args.crop_radius is not None and args.crop_radius <= 0.0:
        raise ValueError("--crop-radius must be positive")
    if (args.camera_eye is None) != (args.camera_target is None):
        raise ValueError("--camera-eye and --camera-target must be used together")
    if args.camera_eye is not None and len(args.camera_eye) != len(args.camera_target):
        raise ValueError("manual camera eye/target counts must match")
    args.output_dir.mkdir(parents=True, exist_ok=False)

    app = AppLauncher(args).app
    try:
        import omni.client
        import isaaclab.sim as sim_utils
        from isaaclab.sim import SimulationCfg, SimulationContext
        from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

        sim = SimulationContext(
            SimulationCfg(device=args.device, dt=1.0 / 120.0, render_interval=1)
        )
        print("[scene-preview] step=resolver_probe", flush=True)
        candidates = candidate_uris(ISAAC_NUCLEUS_DIR, args.scene)
        attempts = []
        selected_uri = None
        for uri in candidates:
            result, entry = omni.client.stat(uri)
            attempts.append({"uri": uri, "result": str(result)})
            if result == omni.client.Result.OK and entry is not None:
                selected_uri = uri
                break
        if selected_uri is None:
            raise RuntimeError(f"no source scene URI resolved: {attempts}")

        hidden_prims = []
        selected_source_prims = []
        if args.subset_reference:
            if args.crop_center is None:
                raise RuntimeError("subset reference requires a spatial crop")
            print(
                f"[scene-preview] step=compose_source_subset uri={selected_uri}",
                flush=True,
            )
            source_stage = Usd.Stage.Open(selected_uri)
            source_root = source_stage.GetDefaultPrim()
            if not source_root.IsValid():
                raise RuntimeError("source scene has no valid default prim")
            source_cache = UsdGeom.BBoxCache(
                Usd.TimeCode.Default(),
                [
                    UsdGeom.Tokens.default_,
                    UsdGeom.Tokens.render,
                    UsdGeom.Tokens.proxy,
                ],
                useExtentsHint=True,
            )
            crop_x, crop_y = (float(value) for value in args.crop_center)
            hidden_names = {
                Path(prim_path).name for prim_path in args.hide_prim
            }
            selected_children = []
            for child in source_root.GetChildren():
                if str(child.GetName()) in hidden_names:
                    hidden_prims.append(
                        f"/World/Environment/{child.GetName()}"
                    )
                    continue
                aligned = source_cache.ComputeWorldBound(child).ComputeAlignedBox()
                lower = aligned.GetMin()
                upper = aligned.GetMax()
                values = tuple(float(value) for value in (*lower, *upper))
                keep = child.IsA(UsdGeom.Camera) or "Light" in child.GetTypeName()
                if all(math.isfinite(value) for value in values):
                    x0, y0, _, x1, y1, _ = values
                    if x1 >= x0 and y1 >= y0:
                        dx = max(x0 - crop_x, 0.0, crop_x - x1)
                        dy = max(y0 - crop_y, 0.0, crop_y - y1)
                        keep = keep or math.hypot(dx, dy) <= args.crop_radius
                    else:
                        keep = True
                else:
                    keep = True
                if keep:
                    selected_children.append(child)
                else:
                    hidden_prims.append(
                        f"/World/Environment/{child.GetName()}"
                    )

            scene_prim = UsdGeom.Xform.Define(
                sim.stage, "/World/Environment"
            ).GetPrim()
            for child in selected_children:
                target_path = scene_prim.GetPath().AppendChild(child.GetName())
                target = sim.stage.OverridePrim(target_path)
                target.GetReferences().AddReference(selected_uri, child.GetPath())
                selected_source_prims.append(str(child.GetPath()))
            del source_stage
        else:
            print(f"[scene-preview] step=spawn_scene uri={selected_uri}", flush=True)
            scene_cfg = sim_utils.UsdFileCfg(usd_path=selected_uri)
            scene_prim = scene_cfg.func("/World/Environment", scene_cfg)
            for prim_path in args.hide_prim:
                prim = sim.stage.GetPrimAtPath(prim_path)
                if not prim.IsValid():
                    raise RuntimeError(
                        f"requested hidden prim is absent: {prim_path}"
                    )
                UsdGeom.Imageable(prim).MakeInvisible()
                hidden_prims.append(prim_path)
        if args.crop_center is not None and not args.subset_reference:
            print("[scene-preview] step=apply_spatial_crop", flush=True)
            crop_cache = UsdGeom.BBoxCache(
                Usd.TimeCode.Default(),
                [
                    UsdGeom.Tokens.default_,
                    UsdGeom.Tokens.render,
                    UsdGeom.Tokens.proxy,
                ],
                useExtentsHint=True,
            )
            crop_x, crop_y = (float(value) for value in args.crop_center)
            for child in scene_prim.GetChildren():
                child_path = str(child.GetPath())
                if child_path in hidden_prims:
                    continue
                aligned = crop_cache.ComputeWorldBound(child).ComputeAlignedBox()
                lower = aligned.GetMin()
                upper = aligned.GetMax()
                values = tuple(float(value) for value in (*lower, *upper))
                if not all(math.isfinite(value) for value in values):
                    continue
                x0, y0, _, x1, y1, _ = values
                if x1 < x0 or y1 < y0:
                    continue
                dx = max(x0 - crop_x, 0.0, crop_x - x1)
                dy = max(y0 - crop_y, 0.0, crop_y - y1)
                if math.hypot(dx, dy) > args.crop_radius:
                    UsdGeom.Imageable(child).MakeInvisible()
                    hidden_prims.append(child_path)
        if args.clay:
            print("[scene-preview] step=apply_clay_material", flush=True)
            material = UsdShade.Material.Define(
                sim.stage, "/World/Looks/PreviewClay"
            )
            shader = UsdShade.Shader.Define(sim.stage, "/World/Looks/PreviewClay/Shader")
            shader.CreateIdAttr("UsdPreviewSurface")
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
                Gf.Vec3f(0.52, 0.58, 0.64)
            )
            shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.82)
            material.CreateSurfaceOutput().ConnectToSource(
                shader.ConnectableAPI(), "surface"
            )
            binding = UsdShade.MaterialBindingAPI.Apply(scene_prim)
            binding.Bind(
                material,
                bindingStrength=UsdShade.Tokens.strongerThanDescendants,
            )
        light_cfg = sim_utils.DomeLightCfg(intensity=900.0, color=(0.9, 0.9, 0.9))
        light_cfg.func("/World/PreviewLight", light_cfg)

        robot_metadata = None
        if args.robot_asset is not None:
            print("[scene-preview] step=spawn_lite3", flush=True)
            robot_cfg = sim_utils.UrdfFileCfg(
                asset_path=str(args.robot_asset.resolve()),
                fix_base=True,
                merge_fixed_joints=False,
                force_usd_conversion=True,
                joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
                    gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(
                        stiffness=None,
                        damping=None,
                    )
                ),
            )
            robot_prim = robot_cfg.func(
                "/World/Lite3",
                robot_cfg,
                translation=tuple(args.robot_position),
            )
            robot_metadata = {
                "prim_path": str(robot_prim.GetPath()),
                "urdf_path": str(args.robot_asset.resolve()),
                "urdf_sha256": _sha256(args.robot_asset),
                "position_m": list(args.robot_position),
                "fixed_base_visual_scale_reference": True,
            }

        print("[scene-preview] step=stage_inventory", flush=True)
        stage = sim.stage
        bounds = _world_bounds(scene_prim)
        print(f"[scene-preview] bounds={bounds}", flush=True)
        views = scene_views(bounds)
        print("[scene-preview] step=replicator_prepare", flush=True)
        for _ in range(20):
            app.update()

        authored_cameras = []
        xform_cache = UsdGeom.XformCache(Usd.TimeCode.Default())
        for prim in stage.Traverse():
            camera_path = str(prim.GetPath())
            if not prim.IsA(UsdGeom.Camera) or camera_path.startswith(
                "/OmniverseKit"
            ):
                continue
            transform = xform_cache.GetLocalToWorldTransform(prim)
            position = transform.ExtractTranslation()
            forward = transform.TransformDir(Gf.Vec3d(0.0, 0.0, -1.0))
            if forward.GetLength() <= 1.0e-9:
                raise RuntimeError(f"authored camera has no forward axis: {camera_path}")
            forward.Normalize()
            target = position + 10.0 * forward
            authored_cameras.append(
                {
                    "path": camera_path,
                    "eye": tuple(float(value) for value in position),
                    "target": tuple(float(value) for value in target),
                }
            )
        files = []
        if args.camera_eye is not None:
            selected_views = [
                (
                    f"manual_{index + 1}",
                    {
                        "eye": tuple(args.camera_eye[index]),
                        "target": tuple(args.camera_target[index]),
                    },
                    None,
                )
                for index in range(len(args.camera_eye))
            ]
        elif args.authored_camera_limit > 0 and authored_cameras:
            selected_views = [
                (f"authored_{index + 1}", camera_record, camera_record["path"])
                for index, camera_record in enumerate(
                    authored_cameras[: args.authored_camera_limit]
                )
            ]
        else:
            selected_views = [
                (name, view, None) for name, view in views.items()
            ]
        for name, view, camera_path in selected_views:
            print(f"[scene-preview] step=capture_{name}", flush=True)
            output = args.output_dir / f"{args.scene}_{name}.png"
            _capture_replicator(
                app,
                output,
                args.width,
                args.height,
                eye=None if view is None else view["eye"],
                target=None if view is None else view["target"],
                camera_prim=None,
                settle_frames=args.settle_frames,
            )
            record = {
                "name": name,
                "path": output.name,
                "bytes": output.stat().st_size,
                "sha256": _sha256(output),
            }
            if view is not None:
                record.update(
                    {
                        key: value
                        for key, value in view.items()
                        if key != "path"
                    }
                )
            if camera_path is not None:
                record["camera_prim"] = camera_path
            files.append(record)

        prims = list(stage.Traverse())
        meshes = [prim for prim in prims if prim.IsA(UsdGeom.Mesh)]
        collision_prims = [
            prim for prim in prims if prim.HasAPI(UsdPhysics.CollisionAPI)
        ]
        rigid_prims = [
            prim for prim in prims if prim.HasAPI(UsdPhysics.RigidBodyAPI)
        ]
        physics_scenes = [prim for prim in prims if prim.IsA(UsdPhysics.Scene)]
        metadata = {
            "status": "runtime_scene_visual_captured",
            "reviewed": False,
            "scene": args.scene,
            "selected_uri": selected_uri,
            "uri_attempts": attempts,
            "asset_root": ISAAC_NUCLEUS_DIR,
            "stage_bounds_xyzxyz_m": bounds,
            "stage_counts": {
                "prims": len(prims),
                "meshes": len(meshes),
                "direct_collision_api_prims": len(collision_prims),
                "rigid_body_api_prims": len(rigid_prims),
                "physics_scenes": len(physics_scenes),
                "authored_cameras": len(authored_cameras),
            },
            "authored_cameras": authored_cameras,
            "hidden_source_prims": hidden_prims,
            "selected_source_prims": selected_source_prims,
            "source_composition_mode": (
                "direct_child_references_from_official_source"
                if args.subset_reference
                else "complete_source_usd_reference"
            ),
            "spatial_crop": (
                None
                if args.crop_center is None
                else {
                    "center_xy_m": list(args.crop_center),
                    "radius_m": args.crop_radius,
                    "hidden_direct_child_count": len(hidden_prims),
                }
            ),
            "robot": robot_metadata,
            "resolution": [args.width, args.height],
            "material_mode": (
                "uniform_clay_override_stronger_than_descendants"
                if args.clay
                else "source_materials"
            ),
            "files": files,
            "claim_boundary": [
                "source USD resolved and rendered on the declared runtime",
                "direct CollisionAPI count is an inventory, not completeness proof",
                "optional fixed-base Lite3 is a visual scale reference only",
                "clay mode preserves source geometry but not source material appearance",
                "no policy, sensor, route, SCAN, or navigation claim",
            ],
        }
        metadata_path = args.output_dir / "capture_metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[scene-preview] metadata={metadata_path}", flush=True)
        print(json.dumps(metadata, ensure_ascii=False), flush=True)
        return 0
    except BaseException:
        traceback.print_exc()
        raise
    finally:
        print("[scene-preview] step=close", flush=True)
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
