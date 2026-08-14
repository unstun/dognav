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

## Automated Gate Record — Human Review Pending

On 2026-08-13, `acceptance_v2_frozen` passed all 51 checks after the preserved
`acceptance_v1_frozen` failure was diagnosed and corrected. The local evidence
is summarized in
`.pipeline/experiments/2026-08-13_scan_foxy_isaac_closed_loop/REPORT.md`.
The evidence label is project `integrated` and fixed-course simulation
`validated` by the frozen automated gate; SCAN upstream remains `surveyed`,
not reproduced on Humble or Noetic. Dr Sun has not yet accepted the video and
evidence bundle. The task therefore remains in `review`, not `completed`.

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
- [ ] **AC11 — Human acceptance:** Dr Sun reviews the complete MP4 and the
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
