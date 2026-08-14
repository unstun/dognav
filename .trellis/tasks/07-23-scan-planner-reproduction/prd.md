# Integrate SCAN-Planner Foxy with Lite3 Physics Simulation

## Goal

Build a traceable simulation-only closed loop in which a ROS 2 Foxy-compatible
port of the SCAN planner drives a policy-controlled Lite3 in Isaac Sim on the
5070 Ti. The result must exercise planning, simulated 3D perception,
policy-driven joint motion, PhysX contacts, and feedback to the planner without
changing the Lite3 onboard Ubuntu 20.04 / ROS 2 Foxy boundary.

The immediate user value is to decide whether the selected planning and
locomotion components can form a credible geometric navigation baseline before
any real-robot work, model training, or LIO integration.

## Confirmed Facts at Planning Freeze

- The target Lite3 onboard software boundary is Ubuntu 20.04 with ROS 2 Foxy.
  Moving the robot to ROS 2 Humble is not part of this task.
- The selected SCAN source is the unofficial `ros2-community` branch of
  `https://github.com/wuyi2121/SCAN-Planner`, pinned at
  `d0b921c9b05a6d291d144d60882b2e0e88d2c0e0`. It targets Ubuntu 22.04,
  ROS 2 Humble, Gazebo Fortress, C++17, and `colcon`; it is not an upstream
  Foxy release.
- That branch contains a contact-capable Go2 Gazebo description, but the
  default planner launch still uses a planar kinematic simulator. The Gazebo
  package does not provide a simulated 3D LiDAR or a complete
  `cmd_vel -> gait -> 12 joints` locomotion path.
- The SCAN planner consumes a 3D point cloud plus time-consistent body and
  sensor pose feedback, and its follower emits body-frame velocity commands.
- The 5070 Ti host currently runs Ubuntu 24.04 with Isaac Sim 5.1 and Isaac Lab
  available in an existing Conda environment. ROS is not installed on the
  host, and no container runtime was present at the latest live inspection.
- Dr Sun permits a one-time privileged environment setup on the 5070 Ti after
  implementation is explicitly approved. Credentials must never be stored in
  the repository, task artifacts, shell history, logs, or scripts.
- The sibling `machine-dog` repository contains Isaac policy runtimes that can
  overwrite the three-component velocity command before policy inference.
  Existing checkpoints and reports are candidates, not proof that a particular
  policy is qualified for this navigation loop.
- SCAN remains `surveyed`; no original Humble run, Foxy port, Lite3 integration,
  or physical closed-loop result has yet been recorded by this project.
- The existing `07-24-lite3-pro-parametric-model` child is an independent CAD
  track. This task neither changes nor depends on its deliverables.

## V2 Automated Gate Record — Baseline Only

On 2026-08-13, `acceptance_v2_frozen` passed all 51 checks after the preserved
`acceptance_v1_frozen` failure was diagnosed and corrected. The local evidence
is summarized in
`.pipeline/experiments/2026-08-13_scan_foxy_isaac_closed_loop/REPORT.md`.
The evidence label is project `integrated` and fixed-course simulation
`validated` by the frozen automated gate; SCAN upstream remains `surveyed`,
not reproduced on Humble or Noetic. Human review found that V2 used the legacy
V12 robot URDF, a task-mounted ray-cast LiDAR, and no simulated D435i. V2 is
therefore preserved as a closed-loop baseline but is no longer the final human
review candidate.

## V3 Reopening Decision

On 2026-08-13, Dr Sun explicitly approved reopening implementation. V3 keeps
the V12 `model_149999` policy, observation, action, actuator, default-pose, and
control contracts unchanged while replacing only the physical robot asset with
the pinned local Lite3 Pro sensor-rig Isaac URDF. V3 must instantiate both a
MID-360-like scene sensor at `mid360_scan_frame` and a D435i-like depth sensor
at `d435i_depth_optical_frame`; visual links without live sensor data do not
satisfy the requirement.

## Requirements

- **R1 — Source provenance.** Preserve the selected SCAN revision as an
  unchanged dated upstream snapshot. Record canonical URL, branch, commit,
  license evidence, dependencies, original run instructions, selected package
  inventory, and every Foxy-specific patch.
- **R2 — Foxy boundary.** Build and run the planner side in an isolated Ubuntu
  20.04 / ROS 2 Foxy environment on the 5070 Ti. Do not install Foxy natively
  on Ubuntu 24.04 and do not rely on cross-distribution DDS compatibility.
- **R3 — Minimal port.** Port only the SCAN planner, map, controller, message,
  and launch/config packages required by the closed loop. Exclude the Humble /
  Fortress Go2 physics package and unrelated simulator assets from the Foxy
  runtime.
- **R4 — Explicit transport.** Connect Foxy and Isaac through a versioned,
  bounded, testable TCP protocol rather than shared ROS middleware. The
  boundary must define frames, units, timestamps, sequence handling, payload
  limits, integrity checks, reconnection behavior, and stale-command shutdown.
- **R5 — Immutable locomotion dependency.** Select and pin one committed
  `machine-dog` source revision and one checkpoint with hashes. Prove that an
  external `[vx, vy, wz]` command reaches the policy observation and changes
  physical motion before connecting the planner. Do not modify or depend on a
  dirty sibling checkout.
- **R6 — Physical simulation.** The Lite3 must move through policy output,
  articulated joints, and PhysX contacts. Base teleportation, direct pose
  integration, or the SCAN kinematic simulator cannot satisfy the physical
  closed-loop gate.
- **R7 — Simulated perception.** Feed SCAN a timestamped 3D point cloud rendered
  from the Isaac scene and synchronized simulator-truth body/sensor poses.
  Scene occlusion and robot motion must affect observations. Static map truth
  cannot be published directly as if it were a sensor.
- **R8 — Safety and boundedness.** Enforce velocity bounds at both sides of the
  bridge, apply latest-command semantics, zero commands after a configurable
  watchdog timeout, and fail closed on malformed, oversized, stale, or
  disconnected input.
- **R9 — Observable closed loop.** Use one deterministic, fixed-seed obstacle
  course and one reachable goal. Record planner output, commanded and measured
  velocity, pose progress, point-cloud health, contact/support evidence,
  collision/termination state, bridge timing, and final goal outcome.
- **R10 — Local evidence.** Treat the local `machine-dog-nav` repository as the
  source of truth. Remote workspaces are execution copies only. Copy manifests,
  configs, patches, hashes, raw logs, metrics, ROS-side recordings, and a
  directly viewable runtime video back into dated project paths before making
  a result claim.
- **R11 — Claim discipline.** Label the Foxy work as a project port, not an
  upstream Foxy release or upstream reproduction. Simulator-truth pose and the
  selected LiDAR model must be named explicitly; neither may be presented as
  Elevator-LIO, real MID-360 parity, or real-robot validation.
- **R12 — Scope control.** Do not start formal training, operate the real robot,
  modify the sibling repository, or alter unrelated dirty worktree paths.
- **R13 — Pinned physical sensor rig.** V3 uses the canonical sensor-rig URDF
  SHA-256 `d0a1be09...cec80` only through its generated Isaac-safe derivative
  SHA-256 `803d5527...bb9d`. Record imported prim names, topology, mass,
  inertia, collision bodies, fixed-joint behavior, and runtime asset hash.
- **R14 — V12 single-variable policy gate.** Keep the V12 checkpoint,
  450-dimensional observation, 12-action ordering, V12 default joint pose,
  actuator gains/limits, timing, and command contract unchanged. Compare the
  legacy and sensor-rig assets with the same seed and command schedule before
  reconnecting SCAN.
- **R15 — Dual simulated sensors.** Instantiate a MID-360-like 3D scene sensor
  at `mid360_scan_frame` and a D435i-like depth sensor at
  `d435i_depth_optical_frame`. Both must generate finite, nonempty,
  pose-dependent data with advancing timestamps from the same physical scene.
- **R16 — Sensor-fidelity boundary.** Record each sensor backend, FOV, sampling
  grid, resolution, range, rate, frame, transform, and occlusion treatment.
  Missing live D435i depth calibration and non-repetitive MID-360 beam timing
  remain explicit limitations; neither sensor may be called hardware parity.
- **R17 — V2 preservation and V3 review.** Do not overwrite V1 or V2 evidence.
  V3 receives a new run identity, thresholds, hashes, logs, ROS recording,
  depth evidence, and MP4. Only V3 may be offered for final human acceptance.

## Acceptance Criteria

- [x] **AC1 — Provenance:** a dated immutable SCAN snapshot and manifest record
  the pinned URL, branch, commit, license evidence, dependencies, original
  commands, selected packages, and SHA-256 hashes.
- [x] **AC2 — Exact environment:** a reproducible Ubuntu 20.04 / ROS 2 Foxy
  runtime on the 5070 Ti is pinned by image digest or equivalent environment
  lock, and its OS, architecture, ROS, compiler, CMake, Python, PCL, and Eigen
  versions are captured without recording credentials.
- [x] **AC3 — Foxy port:** the selected SCAN packages build from a clean Foxy
  workspace, all added unit/integration tests pass, and the Foxy nodes launch
  without Humble, Fortress, or the SCAN kinematic simulator.
- [x] **AC4 — Transport:** automated loopback tests cover complete and partial
  reads, message framing, payload limits, integrity failure, sequence gaps,
  timestamp propagation, reconnects, command saturation, and watchdog stop.
- [x] **AC5 — Locomotion takeover:** a fixed external command schedule visibly
  changes the pinned policy command tensor, policy observation, measured base
  velocity, joint motion, and contact/support signals; command timeout returns
  the simulated robot to zero-command behavior.
- [x] **AC6 — Sensor and frame gate:** the simulated LiDAR produces nonempty,
  finite, advancing point clouds whose geometry changes with scene occlusion
  and robot pose. The Foxy bridge publishes synchronized, frame-consistent
  point cloud and simulator-truth odometry accepted by SCAN.
- [x] **AC7 — Closed-loop result:** from a fixed start and reachable goal, SCAN
  produces a trajectory and bounded nonzero commands; the Lite3 advances via
  policy-driven joint dynamics and valid contacts, avoids the declared
  obstacles, stops at the goal tolerance, and triggers no stale-command,
  collision, NaN, or base-teleport condition.
- [x] **AC8 — Performance record:** the result reports planner rate, policy /
  physics rate, sensor rate, bridge latency, point count, drops or sequence
  gaps, watchdog events, command bounds, path/goal progress, and termination
  reason. Thresholds used for the final gate are frozen before the acceptance
  run.
- [x] **AC9 — Evidence sync:** the complete acceptance configuration, hashes,
  patches, raw stdout/stderr, machine-readable metrics, ROS-side recording, and
  directly viewable MP4 are copied from the 5070 Ti into the local repository
  and verified against remote hashes.
- [x] **AC10 — Honest status:** the final report distinguishes `surveyed`,
  project `integrated`, and simulation `validated` evidence. It explicitly
  states that no upstream Foxy reproduction, real MID-360 parity, LIO result,
  trained navigation policy, or real-robot safety result was established.
- [x] **AC11 — Sensor-rig asset identity:** the exact Isaac-safe URDF imports
  with 24 links, 23 joints, 12 movable joints, the expected sensor frames,
  declared total mass, primitive collisions, and no silent default-mass body.
- [x] **AC12 — V12-on-rig qualification:** with identical V12 policy/control
  inputs, the new asset passes zero, forward, lateral, yaw, support, finite,
  no-termination, and watchdog checks. The A/B report records both old and new
  asset hashes and does not attribute differences without evidence.
- [x] **AC13 — MID-360 simulation gate:** the sensor is bound to
  `mid360_scan_frame`, returns scene-derived 3D points across the declared FOV
  and range, accounts for the pinned rig's self-occlusion through a declared
  backend or geometry mask, and passes frame/timestamp/motion checks.
- [x] **AC14 — D435i simulation gate:** the depth sensor is bound to
  `d435i_depth_optical_frame`, produces finite depth with declared pinhole
  parameters and resolution, observes the physical obstacle, changes with
  pose, and preserves representative raw frames plus metrics.
- [x] **AC15 — V3 closed loop:** after AC11--AC14 pass, one frozen V3 run uses
  MID-360 point data for SCAN while D435i runs concurrently, reaches the goal
  without collision/reset/stale command, and preserves a directly viewable
  video showing the new sensor rig.
- [x] **AC16 — V3 evidence identity:** the run record includes source,
  checkpoint, canonical/Isaac URDF, mesh bundle, sensor configs, transforms,
  thresholds, binaries, logs, ROS bag, depth samples, metrics, and video hashes
  with local/remote parity.
- [ ] **AC17 — Human acceptance:** Dr Sun reviews the complete V3 MP4 and
  evidence bundle, then explicitly records acceptance or rejection. Automated
  checks and agent visual inspection do not satisfy this criterion.

## Stop Conditions

Implementation stops without promoting the evidence label if any of these
conditions remains after the documented fallback is exhausted:

- an isolated Foxy runtime cannot be established without an unapproved host
  change;
- no immutable existing policy/checkpoint can track external velocity commands
  with stable support and no training;
- the simulated LiDAR cannot provide frame-consistent scene observations;
- bridge timing cannot keep commands and sensor feedback within the frozen
  watchdog and latency limits.

The exact blocker, attempted fallback, logs, and next user-owned decision must
be recorded. A blocker report does not satisfy AC7 and must not be called a
validated closed loop.

## Out of Scope

- ROS 2 Humble deployment on the Lite3 onboard computer.
- Cross-distribution ROS 2 DDS as the Foxy–Isaac integration mechanism.
- Original SCAN Humble or ROS 1 Noetic reproduction.
- Elevator-LIO, SLAM/LIO accuracy evaluation, or realistic localization noise.
- Formal policy training, fine-tuning, distillation, or checkpoint selection by
  new training.
- Real-robot actuation, hardware power/cabling, payload CAD, or sensor mounting.
- Calibrated MID-360 noise, coverage, timing, intensity, or weather parity.
- Multi-map, multi-seed, dynamic-obstacle, or comparative benchmark claims.
