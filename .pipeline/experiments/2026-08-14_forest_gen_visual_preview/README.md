# forest_gen Native Isaac Lab Visual Preview

Status: raw Isaac Lab viewport images generated on the RTX 5070 Ti; pending
human visual review. Scene shutdown required an interrupt after the images and
metrics were flushed and synchronized.

This is a review-only upstream reproduction probe. It captures the native
`forest_gen` scene through Isaac Lab and does not modify the upstream source.
It does not test vegetation collision, sensors, planning, Lite3, or the V12
locomotion policy.

## Sources

- `forest_gen` release `v0.3.8`, commit
  `a75fb28c7b896e2a67e2d889b804732d33c56e0c`, GPL-3.0-only
- STRIPE-kit commit `ce97eed40d9fc4927c4856eda6a17204d01087db`,
  GPL-3.0-only
- Local source of truth:
  `references/upstream/2026-08-14_native-isaaclab-forest/source/`

## Execution Boundary

- Remote execution copy:
  `/home/sun/machine-dog-nav-runs/2026-08-14_forest_gen_visual_preview`
- Target runtime: the existing Isaac Sim 5.1 / Isaac Lab 2.3.2 environment on
  the RTX 5070 Ti
- Dependency rule: preserve the runtime NumPy `<2`; expose the pinned sources
  via `PYTHONPATH` and install only the missing `opensimplex==0.4.5.1`
- Expected outputs: three raw PNG viewport captures, metrics JSON, and runtime
  log copied back into this directory with matching SHA-256 hashes

## Planned Remote Command

```bash
PYTHONPATH=<forest_gen>:<STRIPE-kit> \
  /home/sun/IsaacLab/isaaclab.sh -p capture_forest_gen.py \
  --headless --enable_cameras --livestream 2 --device cuda:0 \
  --size 32 --seed 14 --width 1280 --height 720 \
  --asset-path <forest_gen>/models --output-dir <run>/results
```

The source tree is synced from this repository to the remote host. Remote-only
edits or images are not accepted as project evidence.

## Result

The fixed `32 m x 32 m`, seed-14 scene rendered successfully in Isaac Sim 5.1
and Isaac Lab 2.3.2 on the RTX 5070 Ti. Three `1280 x 720` raw viewport PNGs
were copied back with matching remote/local SHA-256 values:

- `results/forest_gen_overview.png`
- `results/forest_gen_robot_context.png`
- `results/forest_gen_canopy.png`

The generated scene contained 41 birches, 46 pines, 50 bushes, 4,484 grass
instances, five rocks, two terrain meshes, and the upstream Spot example for
scale. The first run took approximately nine minutes to reach image capture,
primarily because the implementation registers thousands of grass instances
individually and performs first-use USDZ conversion.

The renderer reported corrupt face-varying UV primvar sizes on several imported
meshes. The images are still decodable and visibly populated, but material/UV
quality is not clean. After image and metrics sync, application teardown did
not finish within six minutes while retaining about 2.7 GiB of GPU memory; the
task-owned process was interrupted and stopped. This preview therefore proves
native scene generation and viewport rendering, not clean lifecycle handling.

The strongest justified label is `reproduced` for the bounded visual-rendering
claim only. Vegetation collision, sensor returns, Lite3, V12, MID-360, D435i,
SCAN-Planner, and navigation performance remain untested in this scene.
