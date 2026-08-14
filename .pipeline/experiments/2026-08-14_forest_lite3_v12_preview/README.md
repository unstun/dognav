# Lite3 V12 native forest preview

Status: **reproduced; awaiting Dr Sun's visual review**.

The review candidate is `runs/results/preview02/forest_lite3_v12.mp4`.
Automated checks passed, but this document does not mark the human-review gate
as accepted.

## Result

The pinned V12 `model_149999.pt` policy ran on the pinned Lite3 Pro sensor-rig
URDF in an Isaac Lab scene built from the `forest_gen` terrain implementation.
The run used PhysX contact dynamics, an MID-360-like multi-mesh ray caster, and
a D435i-like ray-cast depth camera. It executed a bounded
zero -> forward -> yaw -> zero command schedule without termination or a
non-finite policy state.

This establishes a short native forest-terrain locomotion preview. It does not
establish training quality, autonomous navigation, obstacle avoidance,
SCAN-Planner integration, transfer to ROS 2 Foxy, or real-robot safety.

## Immutable identities

| Input | Pinned identity |
| --- | --- |
| V12 checkpoint | `a9d31dce90e6e8c564d955e473d6d3502f893d7ef5a5c1efaf5bb50d6b3d5450` |
| Canonical sensor-rig URDF | `d0a1be09f018c0ab31df26f69ad8e700bd88ec06ae5b0f4dfbcc4fddf21cec80` |
| Isaac-safe sensor-rig URDF | `803d552703bcc4f72ce15f38b95bc3f62e3e4ada0b42bf3ecf71b32b6590bb9d` |
| `forest_gen` | `a75fb28c7b896e2a67e2d889b804732d33c56e0c` |
| STRIPE-kit | `ce97eed40d9fc4927c4856eda6a17204d01087db` |
| forest terrain geometry | `02a062e08fc870fa425672606ad21efdc19a12534dd2733b4d7a00426de18328` |

The terrain hash is identical in `preflight06` and `preview02`.

## Scene composition

- Terrain: the pinned `forest_gen` fractal terrain, microrelief, drainage,
  slope/aspect, moisture, and mesh pipeline on a 32 m x 32 m tile.
- Reproducibility adapter: explicit seed 14 is injected into `FractalNoise`
  and NumPy before microrelief. Upstream v0.3.8 otherwise constructs an
  unseeded `RandomState` for terrain noise and `random.Random(None)` for its
  full population generator.
- Vegetation: 4 pine, 4 birch, 3 rock, 6 bush, and 30 grass visual instances
  use upstream source assets. Their bounded positions are task-owned and
  deterministic; the nondeterministic upstream full population generator is
  not used in this run.
- Collision and sensing: 11 visible trunk/rock proxies are the same prim roots
  used by PhysX, the MID-360-like ray caster, and the D435i-like depth ray
  caster. Grass and bushes remain visual-only.
- Terrain mesh: 32,768 vertices, 32,258 faces, height range
  0.0533-1.9719 m. `TextureVisuals` is converted to `ColorVisuals` before
  TerrainImporter concatenation; vertices and faces are unchanged.

The visible brown cylinders and grey cuboids in the video are deliberate
engineering geometry, not a final photorealistic forest treatment.

## `preview02` automated evidence

| Check | Observed |
| --- | --- |
| Qualification status | `PASS` |
| Policy observations/actions | 450 / 12, strict V12 loader |
| Physics / policy / sensors | 200 Hz / 50 Hz / 10 Hz configured |
| Recorded policy steps | 412 |
| Root XY displacement | 1.350 m |
| Terrain-height range along root path | 0.456 m |
| Minimum base clearance | 0.245 m |
| Supported sample fraction | 0.879 |
| Mean forward body velocity | 0.359 m/s |
| Mean yaw response | 0.306 rad/s |
| MID-360-like records | 83, all nonempty and finite |
| D435i-like depth records | 83, finite and obstacle-visible |
| Static proxy agreement | all 11 pass visible/collision/lidar/depth checks |
| Video | H.264, 1280 x 720, 138 frames, 17 fps, 8.118 s |

The recorded schedule spans 10.257 s of wall time and 8.250 s of simulated
time. The MP4 samples every third policy step and is encoded at 17 fps, so its
8.118 s playback follows simulated steps rather than exact wall-clock timing;
the authoritative phase labels and timings are in `metrics.jsonl`. The trailing
safety window contains one expected watchdog transition (11 stale-command
samples, all zero command), with no termination, non-finite state, or non-foot
contact.

## Run history and negative evidence

- `preflight01`: invalid wrapper success; Python returned zero but no core
  report existed. This caused the runner to require a report and override a
  missing report with exit 90.
- `preflight02` / `preflight03`: the original upstream population path was not
  deterministic and could not always supply the requested safe rock subset.
  Repeated seed-14 runs produced different total populations. The full
  population generator was removed from the reproducible adapter.
- `preflight04`: TerrainImporter rejected `TextureVisuals` during mesh
  concatenation. Visuals were normalized without changing geometry.
- `preflight05`: the V12 command term did not know the new terrain key `main`.
  It now receives the unchanged V12 flat-terrain maximum range while live
  commands remain the recorded fixed preview schedule. The failed run also
  exposed an error-path teardown hang and was terminated after its report was
  safely written.
- `preflight06`: no-video automated preflight passed.
- `preview01`: automated checks passed, but human-facing framing was rejected
  because a foreground tree occluded the robot.
- `preview02`: automated checks passed and the robot remains visible throughout
  the sampled review frames. This is the only human-review candidate.

All failed logs are retained under `runs/logs/`; no failed run was relabelled as
successful.

## Evidence map

- Review video: `runs/results/preview02/forest_lite3_v12.mp4`
- Frozen identity: `runs/results/preview02/isaac/run_identity.json`
- Runtime composition and proxy audit:
  `runs/results/preview02/isaac/runtime_composition.json`
- Automated report: `runs/results/preview02/isaac/qualification_report.json`
- Policy/contact records: `runs/results/preview02/isaac/metrics.jsonl`
- LiDAR records: `runs/results/preview02/isaac/sensor_metrics.jsonl`
- Depth records and artifact: `runs/results/preview02/isaac/depth_metrics.jsonl`
  and `runs/results/preview02/isaac/d435i_depth_frame_metadata.json`
- Human-review frames: `review_frames_preview02/`
- Superseded occluded frames: `review_frames/`
- Execution wrapper: `run_remote_forest_v4.sh`

Remote and local hashes were compared for every `preview02` result and log
file. The lists matched with no differences. The GPU execution copy was
cleanly shut down after `preview02` (180 MiB idle allocation, no owned simulator
process).
