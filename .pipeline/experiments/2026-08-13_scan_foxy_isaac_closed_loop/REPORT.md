# Foxy SCAN to Lite3 Isaac Closed-Loop Report

## Outcome

`acceptance_v2_frozen` passed all 51 checks in the unchanged frozen acceptance
configuration. This is an **automated acceptance result**, not final human
acceptance. Dr Sun's review of the full video and evidence bundle is pending,
so the Trellis task remains in `review` and must not be archived as completed.

Within that boundary, the strongest justified evidence labels are:

- SCAN upstream source: **surveyed** at
  `d0b921c9b05a6d291d144d60882b2e0e88d2c0e0`;
- project Foxy port and TCP/Isaac bridge: **integrated**;
- fixed-seed, fixed-course, ray-cast-LiDAR Isaac scenario: **validated by the
  frozen automated gate**.

This is not an original SCAN Humble/Noetic reproduction and not a real-robot,
MID-360, LIO, localization-noise, multi-seed, or navigation-training result.

## Accepted System Identity

| Component | Accepted identity |
|---|---|
| Planner source | SCAN `ros2-community`, commit `d0b921c9b05a6d291d144d60882b2e0e88d2c0e0`, Apache-2.0 |
| Planner runtime | Ubuntu 20.04.6 / ROS 2 Foxy rootless Podman image `e4aa7154...227d8` |
| Host simulator | Ubuntu 24.04.3, Isaac Sim 5.1 / Isaac Lab, RTX 5070 Ti |
| Locomotion source | V12 commit `8c3fdffa84b85be0704a10ea5b2533817d543822` |
| Checkpoint | `model_149999.pt`, SHA-256 `a9d31dce...3d5450` |
| Sensor | Isaac Lab `MultiMeshRayCaster`, 16 channels, 2 degree horizontal resolution, 10 Hz |
| Pose | simulator-truth body and sensor pose |
| Physical course | flat PhysX terrain, one `0.6 x 1.2 x 0.8 m` collision box centered at `(2, 0, 0.4) m` |
| Goal | `(4, 0, 0.35) m` |
| Acceptance config | SHA-256 `3f08fb8f01573ba97e3f2b4e6a6cd06a3debd4c76def47149d08cfe707f4545d` |

The full image inspection, package list, compiler/library versions, source
hashes, binary hashes, and exact formal invocations are recorded in
`environment/`, the accepted run's `input_sha256.txt`, and
`formal_runs.yaml`.

## Gate Results

### Foxy build and tests

The final seven-package Foxy workspace rebuilt cleanly before the formal run.
The test result was 46 tests, 0 errors, 0 failures, and 0 skipped. The log is
under `runs/acceptance_v2_frozen/logs/formal_v2_preflight_tests/`.
After adding the explicit `builtin_interfaces` package dependency during final
review, the current source candidate rebuilt with the same 46/0/0/0 result;
those logs are under
`runs/acceptance_v2_frozen/logs/post_acceptance_current_source_verify/`.
This metadata-only verification did not modify or reclassify the formal
runtime.

### Locomotion selection

The first V17 E3 candidate was rejected: it exposed the external command and
responded forward, but failed the lateral, yaw, and support qualification
checks. The one allowed V12 fallback passed command visibility, forward,
lateral, yaw, support, finite-policy, no-termination, and watchdog-zero checks.
The raw records are under `gates/locomotion_v17_rejected/` and
`gates/locomotion_v12_qualified/`.

### Sensor and frame qualification

The V12 sensor gate passed finite/nonempty output, advancing timestamps, ground
and obstacle returns, pose-dependent geometry, and pose displacement. The
accepted planner cloud removes traversable floor hits at or below world
`z=0.05 m`; it does not publish static map truth. Raw evidence is under
`gates/sensor_v12_qualified/`.

## Formal Run Metrics

| Metric | V2 value | Frozen gate |
|---|---:|---:|
| Acceptance checks | 51 / 51 | all pass |
| Goal XY error | 0.0327 m | <= 0.12 m |
| Minimum detour within obstacle window | 1.3212 m | >= 0.80 m |
| Maximum non-foot contact | 0 N | <= 75 N |
| Supported-contact fraction | 0.9977 | >= 0.97 |
| Maximum step displacement | 0.0125 m | <= 0.05 m |
| Final stopped planar speed | 0.0163 m/s | <= 0.12 m/s |
| Final command | `[0, 0, 0]` | <= 0.05 per component |
| Planner publications | 2 successful, 0 failed | >= 2, 0 failed |
| Published B-spline event rate | 2.92 Hz over the publication interval | recorded, event-driven |
| Policy rate | 50.000 Hz | 45-55 Hz |
| Physics rate | 200 Hz | recorded runtime |
| Isaac sensor rate | 10.000 Hz | 8-12 Hz |
| ROS cloud/body/sensor observed rate | 8.705 Hz | 8-12 Hz |
| ROS sensor triplet synchronization | 1.0 | >= 0.95 |
| Cloud points | 58-221, mean 121.6 | >= 10 |
| Command latency P95 | 35.23 ms | <= 100 ms |
| Sequence gaps / watchdog / protocol errors | 0 / 0 / 0 | all zero |
| Telemetry reconnects | 0 | <= 1 |
| Simulated path length | 5.545 m | recorded |
| ROS bag bytes | 225,280 | >= 10,000 |

The B-spline figure is an event publication rate, not a periodic planner
throughput benchmark. The accepted integration keeps the 20 Hz collision
safety check and uses event-driven safety replanning.

## Failure-Preserving Run History

The original frozen run was not overwritten. `acceptance_v1_frozen` reached
the goal but failed with a 119.47 N collision, 0.610 m minimum detour, and 304
failed plan attempts. The frozen threshold SHA matched the later accepted run.

Diagnosis established four interacting causes: wall-clock trajectory progress
outpaced articulated locomotion, the Go2-sized planning envelope was too small
for the Lite3 loop, initially occluded volume behind surface returns was treated
as free, and distance-only periodic replanning replaced still-safe paths. The
accepted implementation adds tracking-error time freeze, a 0.50 m/s matched
speed, a 0.40 m Lite3 planning envelope, a 0.70 m occlusion shadow, and
event-driven safety replanning. Two identical-input dry runs passed before V2.

## Evidence Integrity and Visual Review

The 26 formal result/test/log files copied from the 5070 Ti match the remote
SHA-256 values. The 14 recorded task-owned source files also match the local
source of truth. Gate 5 and Gate 6 copied evidence likewise matches remote
hashes.

The accepted MP4 is a regular H.264 file: 1280 x 720, 25 fps, 431 frames,
17.24 seconds, 9,928,439 bytes, SHA-256
`7d954023cc16a5a16d530da5a8250cd68bc27fc2770bdc742bc5ddd12aacf07c`.
Frames sampled at 2, 6, 10, and 15 seconds show articulated locomotion around
the physical red box with no contact or pass-through, followed by stable motion
toward the goal. This agent visual review does not replace Dr Sun's human
acceptance of the full video.

**Human review status: pending.** A later acceptance or rejection must be
recorded in `HUMAN_REVIEW.md`; this report and commit do not decide that
review.

## Remaining Boundary

The result supports proceeding with a geometric navigation baseline in
simulation. It does not establish real sensor calibration/noise, Elevator-LIO
performance, onboard timing, terrain/contact robustness beyond the flat course,
dynamic-obstacle behavior, multi-seed repeatability, or real-robot safety.
