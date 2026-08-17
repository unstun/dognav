"""Capture a source-material global tour of all three authored Office floors."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from isaaclab.app import AppLauncher

from scene_preview_core import (
    OFFICE_FLOOR_LEVELS,
    candidate_uris,
    office_global_camera_pose,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_bounds(cache, prim):
    aligned = cache.ComputeWorldBound(prim).ComputeAlignedBox()
    values = tuple(float(value) for value in (*aligned.GetMin(), *aligned.GetMax()))
    if not all(math.isfinite(value) for value in values):
        return None
    x0, y0, z0, x1, y1, z1 = values
    if x1 < x0 or y1 < y0 or z1 < z0 or max(abs(value) for value in values) > 1000.0:
        return None
    return values


def _overlay(rgb, title: str, subtitle: str):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    image = Image.fromarray(np.asarray(rgb))
    draw = ImageDraw.Draw(image, "RGBA")
    try:
        title_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26
        )
        subtitle_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17
        )
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    draw.rounded_rectangle((18, 16, 430, 83), radius=10, fill=(0, 0, 0, 165))
    draw.text((34, 25), title, fill=(255, 255, 255, 255), font=title_font)
    draw.text((34, 57), subtitle, fill=(210, 225, 240, 255), font=subtitle_font)
    return np.asarray(image)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--seconds-per-floor", type=float, default=6.0)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.width < 640 or args.height < 360:
        raise ValueError("global tour resolution must be at least 640x360")
    if args.fps < 6 or args.fps > 30:
        raise ValueError("global tour fps must be within [6, 30]")
    if args.seconds_per_floor < 4.0 or args.seconds_per_floor > 15.0:
        raise ValueError("seconds per floor must be within [4, 15]")
    args.output_dir.mkdir(parents=True, exist_ok=False)

    app = AppLauncher(args).app
    try:
        import imageio.v2 as imageio
        import numpy as np
        import omni.client
        import omni.replicator.core as rep
        import isaaclab.sim as sim_utils
        from isaaclab.sim import SimulationCfg, SimulationContext
        from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
        from pxr import Usd, UsdGeom

        sim = SimulationContext(SimulationCfg(device=args.device, dt=1.0 / 120.0, render_interval=1))
        selected_uri = None
        attempts = []
        for uri in candidate_uris(ISAAC_NUCLEUS_DIR, "office"):
            result, entry = omni.client.stat(uri)
            attempts.append({"uri": uri, "result": str(result)})
            if result == omni.client.Result.OK and entry is not None:
                selected_uri = uri
                break
        if selected_uri is None:
            raise RuntimeError(f"Office URI did not resolve: {attempts}")

        print(f"[office-global] step=compose_full_interior uri={selected_uri}", flush=True)
        source_stage = Usd.Stage.Open(selected_uri)
        source_root = source_stage.GetDefaultPrim()
        if not source_root.IsValid():
            raise RuntimeError("Office source has no valid default prim")
        cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
            useExtentsHint=True,
        )
        environment = UsdGeom.Xform.Define(sim.stage, "/World/Environment").GetPrim()
        records = []
        selected = []
        hidden = []
        for child in source_root.GetChildren():
            name = str(child.GetName())
            if name == "SM_Buildings":
                hidden.append(str(child.GetPath()))
                continue
            target = sim.stage.OverridePrim(environment.GetPath().AppendChild(child.GetName()))
            target.GetReferences().AddReference(selected_uri, child.GetPath())
            bounds = _finite_bounds(cache, child)
            records.append(
                {
                    "name": name,
                    "source_path": str(child.GetPath()),
                    "target_path": str(target.GetPath()),
                    "bounds": bounds,
                    "common": child.IsA(UsdGeom.Camera)
                    or "Light" in child.GetTypeName()
                    or name in {"DomeLight", "ExtraLights"},
                }
            )
            selected.append(str(child.GetPath()))
        del source_stage

        preview_light_cfg = sim_utils.DomeLightCfg(intensity=700.0, color=(0.9, 0.9, 0.9))
        preview_light_cfg.func("/World/PreviewLight", preview_light_cfg)
        camera_path = "/World/OfficeGlobalCamera"
        UsdGeom.Camera.Define(sim.stage, camera_path)

        floor_records = []
        for label, floor_z in OFFICE_FLOOR_LEVELS:
            floor_mesh_bounds = []
            for record in records:
                bounds = record["bounds"]
                if bounds is None or not record["name"].startswith("SM_Floor"):
                    continue
                center_z = 0.5 * (bounds[2] + bounds[5])
                if abs(center_z - floor_z) <= 0.2:
                    floor_mesh_bounds.append(bounds)
            if not floor_mesh_bounds:
                raise RuntimeError(f"no authored floor meshes found for {label} at z={floor_z}")
            floor_bounds = (
                min(bounds[0] for bounds in floor_mesh_bounds),
                min(bounds[1] for bounds in floor_mesh_bounds),
                max(bounds[3] for bounds in floor_mesh_bounds),
                max(bounds[4] for bounds in floor_mesh_bounds),
            )
            floor_records.append(
                {
                    "label": label,
                    "floor_z_m": floor_z,
                    "bounds_xy_m": floor_bounds,
                    "floor_mesh_count": len(floor_mesh_bounds),
                }
            )
        print(
            "[office-global] floor_inventory="
            + json.dumps(floor_records, ensure_ascii=False),
            flush=True,
        )

        def activate_floor(floor_record):
            floor_z = floor_record["floor_z_m"]
            visible_paths = []
            for record in records:
                prim = sim.stage.GetPrimAtPath(record["target_path"])
                imageable = UsdGeom.Imageable(prim)
                bounds = record["bounds"]
                name = record["name"]
                visible = record["common"]
                if bounds is not None and not record["common"]:
                    z0, z1 = bounds[2], bounds[5]
                    visible = z1 >= floor_z - 0.15 and z0 <= floor_z + 3.15
                    if name.startswith("SM_Floor"):
                        visible = abs(0.5 * (z0 + z1) - floor_z) <= 0.2
                    if "Ceiling" in name or name == "Cube18":
                        visible = False
                if visible:
                    imageable.MakeVisible()
                    visible_paths.append(record["source_path"])
                else:
                    imageable.MakeInvisible()
            return visible_paths

        frames_per_floor = int(round(args.fps * args.seconds_per_floor))
        first_floor = floor_records[0]
        first_visible = activate_floor(first_floor)
        first_eye, first_target = office_global_camera_pose(
            first_floor["bounds_xy_m"], first_floor["floor_z_m"], 0, frames_per_floor
        )
        sim.set_camera_view(first_eye, first_target, camera_prim_path=camera_path)
        render_product = rep.create.render_product(camera_path, (args.width, args.height))
        annotator = rep.AnnotatorRegistry.get_annotator("rgb", device="cpu")
        annotator.attach(render_product)
        data = None
        for _ in range(480):
            app.update()
            candidate = annotator.get_data()
            if getattr(candidate, "size", 0) >= args.width * args.height * 3:
                data = candidate
                break
        if data is None:
            raise RuntimeError("Office global camera did not produce a first frame")
        for _ in range(24):
            app.update()

        video_path = args.output_dir / "office_global_three_floor_tour.mp4"
        keyframes = []
        total_frames = frames_per_floor * len(floor_records)
        print(
            f"[office-global] step=capture floors={len(floor_records)} frames={total_frames}",
            flush=True,
        )
        with imageio.get_writer(
            video_path,
            fps=args.fps,
            codec="libx264",
            quality=8,
            pixelformat="yuv420p",
            macro_block_size=None,
        ) as writer:
            for floor_index, floor_record in enumerate(floor_records):
                visible_paths = first_visible if floor_index == 0 else activate_floor(floor_record)
                floor_record["visible_source_prims"] = visible_paths
                for local_frame in range(frames_per_floor):
                    eye, target = office_global_camera_pose(
                        floor_record["bounds_xy_m"],
                        floor_record["floor_z_m"],
                        local_frame,
                        frames_per_floor,
                    )
                    sim.set_camera_view(eye, target, camera_prim_path=camera_path)
                    app.update()
                    app.update()
                    app.update()
                    array = np.asarray(annotator.get_data())
                    if array.ndim != 3 or array.shape[2] < 3:
                        raise RuntimeError(
                            f"unexpected {floor_record['label']} frame {local_frame}: {array.shape}"
                        )
                    rgb = array[..., :3]
                    if rgb.dtype != np.uint8:
                        maximum = float(np.nanmax(rgb)) if rgb.size else 0.0
                        rgb = np.clip(
                            rgb * (255.0 if maximum <= 1.0 else 1.0), 0.0, 255.0
                        ).astype(np.uint8)
                    display = _overlay(
                        rgb,
                        f"OFFICE GLOBAL | {floor_record['label']}",
                        f"floor z = {floor_record['floor_z_m']:.1f} m | source materials",
                    )
                    writer.append_data(display)
                    if local_frame == 0:
                        keyframe_path = args.output_dir / (
                            f"office_global_{floor_record['label'].lower()}_top.png"
                        )
                        imageio.imwrite(keyframe_path, display)
                        keyframes.append(keyframe_path)
                    if local_frame % args.fps == 0:
                        print(
                            f"[office-global] floor={floor_record['label']} "
                            f"frame={local_frame}/{frames_per_floor}",
                            flush=True,
                        )
        annotator.detach(render_product)

        outputs = []
        for path in (video_path, *keyframes):
            outputs.append({"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)})
        metadata = {
            "status": "office_global_three_floor_source_material_tour_captured",
            "reviewed": False,
            "selected_uri": selected_uri,
            "uri_attempts": attempts,
            "source_composition_mode": "all_office_direct_children_except_city_buildings",
            "material_mode": "source_materials",
            "hidden_source_prims": hidden,
            "selected_source_prims": selected,
            "floor_records": floor_records,
            "resolution": [args.width, args.height],
            "fps": args.fps,
            "frames_per_floor": frames_per_floor,
            "frame_count": total_frames,
            "duration_s": total_frames / args.fps,
            "display_overlay": "floor label and authored floor-z; scene pixels remain Isaac RGB",
            "outputs": outputs,
            "claim_boundary": [
                "actual Isaac Sim moving-camera RGB from three authored Office floor levels",
                "all Office direct children except the distant SM_Buildings context are composed",
                "non-active levels and ceilings are hidden only for floor-plan visibility",
                "no robot, collision completeness, physics, sensor, planner, or navigation claim",
            ],
        }
        metadata_path = args.output_dir / "global_tour_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[office-global] metadata={metadata_path}", flush=True)
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
