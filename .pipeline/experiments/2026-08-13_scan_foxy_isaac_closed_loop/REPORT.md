# Foxy SCAN to Lite3 Isaac Closed-Loop Report

## Outcome

`acceptance_v3_frozen` passed all 71 checks in the frozen V3 acceptance
configuration. A post-sync local re-evaluation also passed all 71 checks, and
the formal result files copied from the 5070 Ti match their remote SHA-256
manifest. This is an **automated fixed-course simulation result**. Human review
is still pending and AC17 is not satisfied.

The strongest justified evidence labels are:

- SCAN upstream source: **surveyed** at
  `d0b921c9b05a6d291d144d60882b2e0e88d2c0e0`;
- project Foxy port, TCP bridge, V12 policy, sensor-rig asset, and dual-sensor
  runtime: **integrated**;
- one fixed-seed, fixed-course V3 Isaac scenario: **validated by the frozen
  automated gate**, pending human review.

V2 remains an immutable baseline because it used the legacy V12 URDF and no
simulated D435i. V3 corrects those omissions by retaining the V12
`model_149999` policy/controller and replacing only the spawn asset with the
pinned sensor-rig URDF, then instantiating live MID-360-like and D435i-like
scene sensors at the imported frames.

This is not an upstream SCAN Foxy release or Humble/Noetic reproduction. It is
not real MID-360 or D435i parity, LIO, localization-noise, multi-seed, terrain,
navigation-training, real-robot, or safety validation.

## V3 System Identity

| Component | V3 identity |
|---|---|
| Planner source | SCAN `ros2-community`, commit `d0b921c9b05a6d291d144d60882b2e0e88d2c0e0`, Apache-2.0 |
| Planner runtime | Ubuntu 20.04.6 / ROS 2 Foxy rootless Podman image `e4aa7154...227d8` |
| Simulator host | Ubuntu 24.04.3, Isaac Sim 5.1 / Isaac Lab, RTX 5070 Ti |
| Locomotion source | V12 commit `8c3fdffa84b85be0704a10ea5b2533817d543822` |
| Checkpoint | `model_149999.pt`, SHA-256 `a9d31dce...3d5450` |
| Canonical sensor-rig URDF | SHA-256 `d0a1be09...cec80` |
| Isaac-safe sensor-rig URDF | SHA-256 `803d5527...bb9d`, fixed joints retained |
| MID-360-like sensor | Isaac Lab `MultiMeshRayCaster`, 16 x 180 rays, -7 to 52 degrees vertical, 2 degree horizontal sampling, 0.1-12 m, 10 Hz, frame `mid360_scan_frame` |
| D435i-like depth | Isaac Lab ray-cast camera, 87 x 58, focal length 24.0, aperture 45.55, 0.1-5 m, 10 Hz, frame `d435i_depth_optical_frame` |
| Pose | simulator-truth body and sensor poses |
| Course | flat PhysX terrain; one `0.6 x 1.2 x 0.8 m` collision box centered at `(2, 0, 0.4) m` |
| Goal | `(4, 0, 0.35) m` |
| Frozen V3 config | SHA-256 `b8f42d04b33532191e8ded21fe705aba33b7cd5c4f1311372e1afcb9561cd9ad` |

## Asset and Locomotion Qualification

Runtime import readback recorded 24 bodies, 23 joints, 12 movable joints,
11 fixed joints, 29 collision prims, and total mass
`13.281788810606713 kg`. Both sensor-frame bodies have explicit `1e-6 kg`
placeholder inertials in the Isaac-safe derivative; no body received a silent
default mass. The canonical asset, Isaac derivative, mesh hashes, per-body
masses/inertias, collision paths, and joint paths are in
`runtime_composition.json`.

The fixed-seed V12 legacy/new-asset A/B qualification passed for both assets
with the same checkpoint, policy class, 450-value observation, 12-action
ordering, default pose, actuator contract, command schedule, seed, and
watchdog. The sensor-rig result had zero non-foot contact, no termination,
finite state, watchdog zeroing, 0.966667 supported-contact fraction, and
directionally correct forward/lateral/yaw response. Numerical differences are
recorded but are not attributed to an individual mass, collision primitive, or
sensor housing.

## Dual-Sensor Qualification

The installed RTX profile inventory contained no Livox or MID-360 profile. A
live RTX module-import probe reached the post-Isaac-app import marker but did
not complete clean output/teardown. The run therefore uses the declared
Isaac Lab multi-mesh ray-cast backend; it does not substitute another vendor's
profile or claim RTX/Livox hardware fidelity.

For LiDAR self-occlusion, rays are checked against the moving rig's visual
geometry. Using broad collision proxies was preserved as a failed preflight
because it incorrectly blocked every environmental ray. In the formal run:

- 173 LiDAR frames advanced at 10 Hz;
- planner point counts ranged from 27 to 227;
- every frame recorded 467 blocked self rays;
- the scan changed with robot motion and retained scene obstacle returns;
- SCAN consumed only this MID-360-like point stream.

The D435i-like depth camera ran concurrently and was not fused into SCAN:

- 173 depth frames advanced at 10 Hz at 87 x 58 pixels;
- valid depth pixels ranged from 3,506 to 4,346;
- the physical obstacle occupied up to 1,346 pixels;
- representative float-depth, millimetre PNG, preview PNG, metadata, and
  per-frame metrics were preserved;
- the intrinsics are provisional because no live D435i depth `CameraInfo` was
  recorded, and color intrinsics were deliberately not reused.

## Dry Runs and Threshold Freeze

`v3_dryrun01` reached the goal without collision but failed three ROS
wall-clock topic-rate checks at approximately 7.986 Hz against the unchanged
8 Hz lower bound. The cause was V3-only video capture load at 25 fps with a
two-policy-step stride. Thresholds were not relaxed. V3 video capture was
changed to 17 fps with a three-step stride; locomotion, planner, sensor, and
acceptance thresholds stayed unchanged.

`v3_dryrun02` and `v3_dryrun03` then passed all 71 checks with identical input
hashes and configuration. Only after those passes was
`acceptance_thresholds_v3.json` frozen on 2026-08-14T04:09:33Z.

## Formal V3 Metrics

| Metric | V3 value | Frozen gate |
|---|---:|---:|
| Acceptance checks | 71 / 71 | all pass |
| Goal XY error | 0.07921 m | <= 0.12 m |
| Minimum detour within obstacle window | 1.38690 m | >= 0.80 m |
| Maximum non-foot contact | 0 N | <= 75 N |
| Policy rate | 50.000 Hz | 45-55 Hz |
| Isaac LiDAR rate | 10.000 Hz | 8-12 Hz |
| LiDAR frames / points | 173 / 27-227 | finite, nonempty, advancing |
| Depth frames / valid pixels | 173 / 3,506-4,346 | finite, nonempty, advancing |
| Command latency P95 | 35.73 ms | <= 100 ms |
| Sequence gaps / watchdog / protocol errors | 0 / 0 / 0 | all zero |
| Final position | `(4.07850, 0.01061, 0.29069) m` | recorded |
| ROS bag bytes | 225,280 | >= 10,000 |

The formal H.264 video is 1280 x 720, 17 fps, 288 frames, 16.941176 seconds,
8,770,191 bytes, SHA-256
`db230a6e5460c8db09a95a1742f435169bf4e32fbdc4f980ba085afc3903d26d`.
Sampled frames show articulated locomotion around the physical red obstacle
and make the top sensor rig visible. Agent inspection does not replace review
of the complete video by Dr Sun.

## Evidence Integrity

All 22 formal result-file hashes match the remote manifest. The five formal
log hashes also match their remote values. The copied video decodes locally,
the ROS bag metadata and SQLite payload are present, the depth array is finite,
and JSON/JSONL artifacts parse. Running the acceptance evaluator again against
the local copies and the frozen V3 config produced 71/71 PASS in
`runs/acceptance_v3_frozen/local_acceptance_recheck.json`.

The complete artifact map is in
`runs/acceptance_v3_frozen/V3_EVIDENCE_MANIFEST.md`. V1, V2, failed V3
preflights, and `v3_dryrun01` remain preserved as negative or baseline
evidence.

## Human Gate and Remaining Boundary

**Human review status: pending.** `HUMAN_REVIEW.md` is the decision record. The
task may move to `review`, but it must not be archived or called human-accepted
until Dr Sun records an explicit decision.

The result supports a geometric navigation baseline in this one simulation
scenario. It does not establish calibrated sensor noise/timing/intensity,
non-repetitive Livox scanning, real D435i intrinsics, Elevator-LIO performance,
onboard timing, terrain/contact robustness, dynamic obstacles, repeatability
across seeds/maps, or real-robot safety.
