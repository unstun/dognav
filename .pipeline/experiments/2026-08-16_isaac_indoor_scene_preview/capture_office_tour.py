"""Capture a bounded Office reception-area camera tour on Isaac Sim.

The source Office USD and materials remain unchanged.  The output is a visual
reception-subset tour only; it is not a complete-office or navigation result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from isaaclab.app import AppLauncher

from scene_preview_core import (
    OFFICE_TOUR_CAMERA_WAYPOINTS,
    candidate_uris,
    office_tour_camera_pose,
)


OFFICE_CROP_CENTER = (-2.0, 3.0)
OFFICE_CROP_RADIUS = 4.0
OFFICE_CONTEXT_PRIMS = {"Camera", "Camera_2", "DomeLight", "ExtraLights", "SM_Buildings"}

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--duration", type=float, default=12.0)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()

    if args.width < 640 or args.height < 360:
        raise ValueError("tour resolution must be at least 640x360")
    if args.fps < 6 or args.fps > 30:
        raise ValueError("tour fps must be within [6, 30]")
    if args.duration < 4.0 or args.duration > 30.0:
        raise ValueError("tour duration must be within [4, 30] seconds")
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

        print(f"[office-tour] step=compose_subset uri={selected_uri}", flush=True)
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
        selected = []
        hidden = []
        crop_x, crop_y = OFFICE_CROP_CENTER
        for child in source_root.GetChildren():
            name = str(child.GetName())
            keep = name in OFFICE_CONTEXT_PRIMS or child.IsA(UsdGeom.Camera) or "Light" in child.GetTypeName()
            aligned = cache.ComputeWorldBound(child).ComputeAlignedBox()
            values = tuple(float(value) for value in (*aligned.GetMin(), *aligned.GetMax()))
            if all(math.isfinite(value) for value in values):
                x0, y0, _, x1, y1, _ = values
                if x1 >= x0 and y1 >= y0:
                    dx = max(x0 - crop_x, 0.0, crop_x - x1)
                    dy = max(y0 - crop_y, 0.0, crop_y - y1)
                    keep = keep or math.hypot(dx, dy) <= OFFICE_CROP_RADIUS
            if keep:
                target = sim.stage.OverridePrim(environment.GetPath().AppendChild(child.GetName()))
                target.GetReferences().AddReference(selected_uri, child.GetPath())
                selected.append(str(child.GetPath()))
            else:
                hidden.append(str(child.GetPath()))
        del source_stage

        sim_utils.DomeLightCfg(intensity=900.0, color=(0.9, 0.9, 0.9)).func(
            "/World/PreviewLight", sim_utils.DomeLightCfg(intensity=900.0, color=(0.9, 0.9, 0.9))
        )
        camera_path = "/World/OfficeTourCamera"
        UsdGeom.Camera.Define(sim.stage, camera_path)
        sim.set_camera_view(*OFFICE_TOUR_CAMERA_WAYPOINTS[0], camera_prim_path=camera_path)

        render_product = rep.create.render_product(camera_path, (args.width, args.height))
        annotator = rep.AnnotatorRegistry.get_annotator("rgb", device="cpu")
        annotator.attach(render_product)
        data = None
        for _ in range(360):
            app.update()
            candidate = annotator.get_data()
            if getattr(candidate, "size", 0) >= args.width * args.height * 3:
                data = candidate
                break
        if data is None:
            raise RuntimeError("Office tour camera did not produce a first frame")
        for _ in range(24):
            app.update()

        frame_count = int(round(args.fps * args.duration))
        video_path = args.output_dir / "office_reception_tour.mp4"
        first_frame_path = args.output_dir / "office_reception_first.png"
        middle_frame_path = args.output_dir / "office_reception_middle.png"
        last_frame_path = args.output_dir / "office_reception_last.png"
        selected_frame_paths = {
            0: first_frame_path,
            frame_count // 2: middle_frame_path,
            frame_count - 1: last_frame_path,
        }
        print(f"[office-tour] step=capture frames={frame_count}", flush=True)
        with imageio.get_writer(
            video_path,
            fps=args.fps,
            codec="libx264",
            quality=8,
            pixelformat="yuv420p",
            macro_block_size=None,
        ) as writer:
            for frame_index in range(frame_count):
                eye, target = office_tour_camera_pose(frame_index, frame_count)
                sim.set_camera_view(eye, target, camera_prim_path=camera_path)
                app.update()
                app.update()
                app.update()
                array = np.asarray(annotator.get_data())
                if array.ndim != 3 or array.shape[2] < 3:
                    raise RuntimeError(f"unexpected frame {frame_index} shape: {array.shape}")
                rgb = array[..., :3]
                if rgb.dtype != np.uint8:
                    maximum = float(np.nanmax(rgb)) if rgb.size else 0.0
                    rgb = np.clip(rgb * (255.0 if maximum <= 1.0 else 1.0), 0.0, 255.0).astype(np.uint8)
                writer.append_data(rgb)
                if frame_index in selected_frame_paths:
                    imageio.imwrite(selected_frame_paths[frame_index], rgb)
                if frame_index % args.fps == 0:
                    print(f"[office-tour] frame={frame_index}/{frame_count}", flush=True)
        annotator.detach(render_product)

        outputs = []
        for path in (video_path, first_frame_path, middle_frame_path, last_frame_path):
            outputs.append({"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)})
        metadata = {
            "status": "office_reception_source_material_tour_captured",
            "reviewed": False,
            "selected_uri": selected_uri,
            "uri_attempts": attempts,
            "source_composition_mode": "direct_child_references_from_official_source",
            "material_mode": "source_materials",
            "crop_center_xy_m": list(OFFICE_CROP_CENTER),
            "crop_radius_m": OFFICE_CROP_RADIUS,
            "selected_source_prims": selected,
            "hidden_source_prims": hidden,
            "camera_waypoints": [
                {"eye": eye, "target": target} for eye, target in OFFICE_TOUR_CAMERA_WAYPOINTS
            ],
            "resolution": [args.width, args.height],
            "fps": args.fps,
            "frame_count": frame_count,
            "duration_s": frame_count / args.fps,
            "outputs": outputs,
            "claim_boundary": [
                "actual Isaac Sim offscreen camera motion and source-material RGB frames",
                "4 m reception subset with official city context, not the complete Office interior",
                "no robot, collision, physics, sensor, planner, or navigation claim",
            ],
        }
        metadata_path = args.output_dir / "tour_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[office-tour] metadata={metadata_path}", flush=True)
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
