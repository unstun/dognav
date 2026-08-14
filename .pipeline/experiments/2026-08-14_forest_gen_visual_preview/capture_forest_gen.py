"""Capture review-only images from the pinned native Isaac Lab forest scene.

This wrapper does not modify forest_gen. It launches the upstream scene through
Isaac Lab, fixes the Python and NumPy random seeds, and saves three viewport
renders for human review. It is not a collision, sensor, navigation, or Lite3
integration test.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import random
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from isaaclab.app import AppLauncher


def _wait_for_file(app: Any, path: Path, frames: int = 120) -> None:
    for _ in range(frames):
        app.update()
        if path.exists() and path.stat().st_size > 0:
            return
        time.sleep(0.01)
    raise RuntimeError(f"viewport capture did not create {path}")


def _drive_capture(
    app: Any,
    capture: Any,
    path: Path,
    timeout_s: float = 30.0,
) -> None:
    """Advance Kit while the asynchronous viewport capture completes."""

    wait = getattr(capture, "wait_for_result", None)
    if not callable(wait):
        _wait_for_file(app, path)
        return

    result = wait()
    if not inspect.isawaitable(result):
        _wait_for_file(app, path)
        return

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    task = asyncio.ensure_future(result, loop=loop)
    deadline = time.monotonic() + timeout_s
    while not task.done() and time.monotonic() < deadline:
        app.update()
        loop.run_until_complete(asyncio.sleep(0))
        if path.exists() and path.stat().st_size > 0:
            return
        time.sleep(0.01)

    if not task.done():
        task.cancel()
        loop.run_until_complete(asyncio.sleep(0))
        raise RuntimeError(f"viewport capture timed out for {path}")

    task.result()
    _wait_for_file(app, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset_counts(names: list[str]) -> dict[str, int]:
    counts = Counter(name.split("_", 1)[0] for name in names)
    return dict(sorted(counts.items()))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture the pinned forest_gen scene in Isaac Lab"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--asset-path", type=Path, required=True)
    parser.add_argument("--size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=14)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()

    if args.size < 24:
        raise ValueError("forest size must be at least 24 m for the 10 m margin")
    if args.width < 320 or args.height < 240:
        raise ValueError("capture resolution is too small for visual review")
    if not args.asset_path.is_dir():
        raise FileNotFoundError(f"asset directory not found: {args.asset_path}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    random.seed(args.seed)
    np.random.seed(args.seed)

    simulation_app = AppLauncher(args).app

    try:
        import omni.kit.viewport.utility as viewport_util
        from isaaclab.scene import InteractiveScene
        from isaaclab.sim import SimulationCfg, SimulationContext
        from isaaclab_assets.robots.spot import SPOT_CFG

        from forest_gen import ForestGenSpec

        sim = SimulationContext(SimulationCfg(device=args.device))
        generator = ForestGenSpec(
            size=args.size,
            asset_path=str(args.asset_path.resolve()),
        )
        scene_factory = generator.create_instance(num_envs=1, env_spacing=1.0)
        scene = InteractiveScene(scene_factory.get_scene(SPOT_CFG))
        sim.reset()
        sim.pause()

        viewport = viewport_util.get_active_viewport()
        if viewport is None:
            raise RuntimeError(
                "no active viewport; launch with --headless --enable_cameras "
                "--livestream 2"
            )
        viewport.set_texture_resolution((int(args.width), int(args.height)))

        for _ in range(30):
            try:
                sim.render()
            except Exception:
                pass
            simulation_app.update()

        origin_x, origin_y = (float(v) for v in generator.origin)
        side = float(args.size)
        views = {
            "overview": (
                (side * 0.50, -side * 0.38, side * 0.45),
                (side * 0.50, side * 0.50, 1.8),
            ),
            "robot_context": (
                (origin_x - 7.0, origin_y - 9.0, 4.8),
                (origin_x, origin_y, 1.2),
            ),
            "canopy": (
                (side * 0.50, side * 0.50, side * 0.92),
                (side * 0.50, side * 0.50, 0.5),
            ),
        }

        files: dict[str, dict[str, Any]] = {}
        for name, (eye, target) in views.items():
            sim.set_camera_view(eye=eye, target=target)
            for _ in range(12):
                try:
                    sim.render()
                except Exception:
                    pass
                simulation_app.update()
            output_path = args.output_dir / f"forest_gen_{name}.png"
            capture = viewport_util.capture_viewport_to_file(
                viewport, str(output_path)
            )
            _drive_capture(simulation_app, capture, output_path)
            files[name] = {
                "path": output_path.name,
                "bytes": output_path.stat().st_size,
                "sha256": _sha256(output_path),
                "eye": eye,
                "target": target,
            }
            print(f"[forest-preview] {name}={output_path}", flush=True)

        metrics = {
            "status": "isaac_raw_generated",
            "reviewed": False,
            "task": "forest_gen visual preview only; no training",
            "forest_gen_commit": (
                "a75fb28c7b896e2a67e2d889b804732d33c56e0c"
            ),
            "stripe_kit_commit": (
                "ce97eed40d9fc4927c4856eda6a17204d01087db"
            ),
            "seed": int(args.seed),
            "size_m": int(args.size),
            "resolution": [int(args.width), int(args.height)],
            "forest_origin_xy": [origin_x, origin_y],
            "asset_counts": _asset_counts(list(scene_factory.assets)),
            "asset_total_including_lights": len(scene_factory.assets),
            "terrain_mesh_count": len(scene_factory.terrain.mesh),
            "robot": "Isaac Lab SPOT_CFG (upstream example; not Lite3)",
            "claim_boundary": [
                "raw viewport images from a live Isaac Lab scene",
                "vegetation collision is not established",
                "Lite3, v12, MID-360, D435i, and SCAN are not integrated",
            ],
            "files": files,
        }
        metrics_path = args.output_dir / "capture_metrics.json"
        metrics_path.write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[forest-preview] metrics={metrics_path}", flush=True)
        return 0
    finally:
        simulation_app.close()


if __name__ == "__main__":
    raise SystemExit(main())
