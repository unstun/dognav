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

## V4 Forest Locomotion Preview Decision

On 2026-08-14, after reviewing raw native `forest_gen` viewport images, Dr Sun
explicitly approved a bounded follow-up: replace the upstream Spot example with
the pinned V3 Lite3 Pro sensor-rig URDF, load the unchanged V12
`model_149999` checkpoint, and produce a short physical policy-inference video
inside a fixed forest scene. V4 is a human-review preview, not a new frozen
SCAN acceptance run. V1--V3 evidence remains immutable.

## V5 Forest Closed-Loop Revision Decision

On 2026-08-14, Dr Sun reviewed the V4 preview and requested two concrete
changes: visibly faster motion and obstacle avoidance. V4 therefore remains a
reproduced open-loop forest locomotion baseline but is not the accepted review
candidate. V5 reconnects the existing Foxy SCAN closed loop, raises the
commanded forward limit from the V4 preview's 0.25 m/s to the already-qualified
0.50 m/s SCAN/V12 limit, and places one declared tree proxy directly across the
start-to-goal line. Avoidance must be caused by SCAN trajectory generation and
replanning from MID-360-like point data; a pre-scripted yaw sequence cannot
satisfy V5.

## V6 One-Metre-Per-Second Review Decision

On 2026-08-14, Dr Sun reviewed the V5 candidate and requested a new V6 rather
than accepting V5: raise the clear-path target to 1.0 m/s, correct the apparent
rock/terrain or rock/proxy interpenetration visible in the video, and show the
SCAN planned trajectory together with the physical Lite3 root trajectory. V5
remains immutable evidence and is recorded as human change-requested. V6 keeps
the pinned V12 `model_149999`, sensor-rig URDFs, forest seed, Foxy boundary,
SCAN algorithm, and physical-policy loop; it is a new simulation candidate,
not a relabeling or overwrite of V5.

The V6 automated result was frozen on 2026-08-14 after two same-input passing
dry runs. `forest_v6_review_candidate01` passed 100/100 but was preserved and
superseded because its run identity retained an obsolete geometry-method
description. The metadata-corrected `forest_v6_review_candidate02` rerun also
passed 100/100 with a 0.967 m/s high-command physical-speed P75, 0.831 m
blocker-centre clearance, 0.039 m goal error, real-mesh rock support evidence,
hidden registered proxies, and a hashed planned-versus-actual overlay.
AC30--AC33 are satisfied; AC34 remains entirely human-owned.

## V7 Dynamic-Obstacle Review Decision

On 2026-08-14, Dr Sun requested a dynamic obstacle after the V6 automated
candidate was delivered. V6 therefore remains immutable, automated-pass
evidence but is not the accepted final review candidate. V7 adds one
deterministic moving rigid obstacle that crosses the robot's nominal route in
the existing forest scene. The same visible and collidable prim must be
observed through the MID-360-like and D435i-like simulated sensors; its points
must not be injected into SCAN and its ground-truth pose must not be used to
steer the robot. The V12 weights, robot URDF, sensor rig, 1.0 m/s ceiling,
forest identity, start/goal, transport, and SCAN algorithms remain unchanged.

V7 evaluates reactive moving-occupancy avoidance: SCAN may replace its active
trajectory or stop after current sensor measurements update the occupancy map.
It does not add or claim obstacle-velocity prediction, intention estimation,
or a generally validated dynamic-navigation benchmark.

## V8 Official-Human Dynamic-Obstacle Decision

On 2026-08-14, after V7 candidate 03 was delivered for review, Dr Sun approved
an independent V8 that replaces the orange cylinder appearance with a yellow
human-shaped moving obstacle. V7 code, runs, thresholds, videos, and pending
human-review record remain immutable; the request does not retroactively accept
V7. V8 preserves the V7 schedule, SCAN map/controller adaptations, forest,
start/goal, V12 policy, Lite3 sensor-rig URDF, dual-sensor settings, and 1.0 m/s
boundary. Only the moving actor representation and the evidence needed to prove
that representation are changed.

The first V8 candidate used a locally generated segmented humanoid and passed
its automated gates, but Dr Sun rejected that representation on 2026-08-14 and
required a ready-made Isaac human instead of a hand-authored model. That
candidate is immutable negative evidence and cannot be submitted or accepted.

V8 R2 references NVIDIA's versioned Isaac Sim 5.1 character
`male_adult_police_04` and the official Biped AnimationGraph from the versioned
Isaac People asset root. The repository records the exact asset URLs,
runtime extension versions, file hashes where the server permits byte reads,
and license boundary; it does not vendor or redistribute NVIDIA character
content. A hidden terrain-seated capsule remains the conservative collision and
clearance proxy because the official skinned character is a visual/animation
asset rather than a stable rigid-body pedestrian. The visual and proxy use
separate roots with separate shoe-sole and capsule-centre vertical datums, but
share the same schedule time, XY position, and heading. The proxy remains absent
from the rendered image.
SCAN receives only geometry returned by the declared simulated sensors; actor
truth, semantic identity, and commanded motion remain evidence-only.

## V8 R2 Auxiliary Immediate-Walk Trial Decision

On 2026-08-15, Dr Sun observed that the continuous-walk visual still waited for
the robot because the physical pedestrian schedule retained the frozen
command-relative trigger. The requested auxiliary trial starts the pedestrian
schedule at closed-loop run start, removes the mid-route hold, and keeps a
constant 0.8 m/s straight-line velocity until the declared endpoint. The
official walk clip remains continuous. This trial intentionally differs from
R34/R40 and cannot replace, pass, or modify the frozen V8 R2 candidate or AC44.

Dr Sun rejected preview 05 after observing that the kinematic human crossed a
source rock and that no SCAN trajectory was published after the human entered
the active local path. The next auxiliary candidate must therefore pass both a
static swept-route geometry precheck and a stronger post-run causal local-plan
replacement audit. Sensor visibility and robot-human clearance alone are not
sufficient.

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
- **R12a — Immediate-walk trial isolation.** A run-start pedestrian trigger may
  be exposed only as an explicit, recorded auxiliary mode whose default remains
  the command-relative trigger. Its run must record zero wait, zero hold,
  constant crossing speed, phase/velocity samples, and the absence of an
  acceptance report.
- **R12b — Immediate-walk geometry and planning causality.** Before rendering,
  the full pedestrian swept capsule must retain positive declared clearance
  from every static forest collision proxy, including each registered rock.
  After rendering, evidence must show sensor detection, the pedestrian entering
  the then-active SCAN path envelope, and a later distinct B-spline with a
  measurable geometry change. A pre-existing static-obstacle plan does not
  satisfy this requirement.
- **R12c — Native voxel-review evidence.** An auxiliary voxel video must be
  derived only from SCAN's published `/grid_map/occupancy` and
  `/grid_map/occupancy_inflate` PointCloud2 messages, with the sliding-map
  bounds, body pose, and B-spline recorded from the same run. Scene truth,
  forest proxy bounds, and Isaac obstacle identity may not create or edit a
  displayed voxel. Preserve the source topics in rosbag, record frame timing
  and point counts, and keep the raw Isaac video beside the derived voxel MP4.
  The primary voxel view must render the native XYZ coordinates against labeled
  X/Y/Z axes with unit vertical scale and a moving perspective camera. A
  top-down or oblique 2-D projection may be retained only as an explicitly
  labeled auxiliary inset; it does not satisfy the 3-D review requirement.
- **R12d — Humble RViz is a replay-only client.** An isolated RoboStack Humble
  RViz2 environment may run on the Apple Silicon Mac only to replay copied Foxy
  evidence. SCAN planning, occupancy construction, controller execution, and
  Foxy--Isaac transport remain in the pinned 5070 Ti runtimes. The replay may
  expose standard `nav_msgs/Path` topics derived from the recorded B-spline and
  body odometry, but it may not change points, timestamps, trajectory geometry,
  or claim cross-distribution DDS integration. Record the exact osx-arm64
  package set and keep the environment isolated from the project Python tools.
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
- **R18 — V4 single-variable composition.** Reuse the exact V3 canonical and
  Isaac-safe URDF hashes, V12 checkpoint hash, 450-dimensional observation,
  12-action order, default pose, actuator settings, control/physics timing, and
  sensor contracts. The intended changes are the forest scene and the declared
  bounded V4 zero/forward/yaw/zero review schedule; neither changes the policy.
- **R19 — Forest source identity.** Use `forest_gen` `v0.3.8` commit
  `a75fb28c7b896e2a67e2d889b804732d33c56e0c` with STRIPE-kit commit
  `ce97eed40d9fc4927c4856eda6a17204d01087db`, a recorded scene seed, and a
  task-owned adapter. Preserve the upstream source unchanged.
- **R20 — Physical and perceptual obstacle agreement.** A declared set of
  visible trunks or rocks near the review route must have explicit collision
  proxies and appear in the declared MID-360-like/D435i-like scene geometry.
  Visible-only vegetation cannot satisfy the forest locomotion gate. Grass is
  visual-only and must not create thousands of physics or ray-cast bodies.
- **R21 — Bounded policy preview.** Run one environment with a short frozen
  zero/forward/yaw/zero command sequence. Record policy input/action, root
  motion, contacts, support, termination/reset state, collision events, and a
  directly viewable MP4. Do not train, tune, connect SCAN, or issue manual
  commands during the run.
- **R22 — Honest V4 claim.** The strongest possible result is a forest
  locomotion preview with the pinned policy and robot asset. It is not a SCAN
  forest-navigation validation, a sensor hardware-parity result, or real-robot
  evidence. Human visual review remains required.
- **R23 — V4 review disposition.** Preserve `preview02` and its automated PASS
  unchanged, but record Dr Sun's explicit change request. Do not relabel V4 as
  accepted or overwrite its video, metrics, or run identity.
- **R24 — Faster frozen limit.** V5 uses the previously qualified SCAN planner
  and controller forward limit of 0.50 m/s, with the V12 transport bound still
  0.75 m/s. The run must record the planner command, policy-visible command,
  measured planar velocity, and timing; changing policy weights, gains, or
  control rates to obtain speed is forbidden.
- **R25 — Terrain-only point filtering.** Forest ground removal must operate
  only on the rendered point geometry and sensor pose. It may use deterministic
  local-minimum/slope logic, but not the terrain height function, USD prim IDs,
  proxy bounds, or scene-truth obstacle labels to choose the points delivered
  to SCAN. Raw finite hits, filtered ground points, and planner points must all
  remain recorded.
- **R26 — Direct-path blocker.** A declared tree with one shared visible,
  collision, MID-360-like, and D435i-like proxy root must intersect the direct
  start-to-goal corridor after applying the frozen Lite3 planning envelope.
  The goal and blocker identity are fixed before the first closed-loop dry run.
- **R27 — Planner-caused avoidance.** The Foxy process must publish the
  trajectory and `cmd_vel`; the Isaac runtime may only consume the received
  command. Acceptance requires a sensor-observed blocker, at least one
  obstacle-driven replacement trajectory, measurable lateral detour and
  physical clearance, zero non-foot collision, and final goal stop.
- **R28 — V5 evidence and claim.** Preserve failed preflights and at least two
  identical-input passing dry runs before freezing a review candidate. Sync
  configs, hashes, binaries, logs, ROS bag, raw metrics, depth evidence, and a
  directly viewable MP4 locally. The strongest claim remains a single-seed
  project-integrated forest simulation pending human review.
- **R29 — V5 review disposition.** Preserve every V5 artifact and record Dr
  Sun's visual change request. Do not edit the V5 video, thresholds, reports,
  or run identity to make it appear to satisfy V6.
- **R30 — V6 speed contract.** Use a 1.0 m/s clear-path forward ceiling at the
  SCAN optimizer, trajectory follower, Foxy bridge, and Isaac receiver while
  preserving the checkpoint, observation/action ordering, policy gains,
  control rate, and 0.5 m/s2 acceleration bound. Record that 1.0 m/s is the
  declared V12 obstacle-terrain training boundary, not a previously validated
  navigation speed. Commands may and should slow for turns, braking, and
  obstacle clearance.
- **R31 — Forest geometry seating.** Diagnose the V5 visual defect from the
  runtime stage before changing placement. V6 must record source-visual world
  bounds, paired collision/sensor-proxy bounds, sampled terrain support
  heights, and clearance. Final review rendering must not expose a simplified
  proxy through the source rock or leave a source visual visibly below the
  terrain, while the registered proxy remains active for PhysX and both
  simulated sensors.
- **R32 — Trajectory provenance and display.** Record complete SCAN B-spline
  order, knots, control points, trajectory ID, and timing plus the Isaac PhysX
  root positions used by each video frame. Produce a review MP4 that displays
  the sampled active SCAN path and accumulated physical root path in distinct,
  labeled colours. A hand-drawn or goal-to-start interpolation is forbidden.
- **R33 — V6 evidence and claim.** Preserve diagnosis/preflight failures,
  obtain at least two identical-input passing dry runs before freezing V6
  thresholds, then run one uninterrupted review candidate. Sync the raw video,
  trajectory-overlay video, trace data, geometry audit, ROS bag, metrics,
  configs, and hashes locally. Automated PASS never satisfies human review.
- **R34 — Deterministic moving rigid body.** V7 adds one visible, collidable,
  terrain-seated cylinder or person-shaped proxy with a frozen
  command-relative wait/cross/hold/cross schedule. The schedule remains at its
  start until the first accepted nonzero body command, avoiding dependence on
  simulator startup time. Isaac PhysX owns its runtime pose; every commanded
  pose and actual simulator readback is recorded. Robot-root writes, scripted
  robot turns, and collision-disabled visual animation cannot satisfy this
  requirement.
- **R35 — Sensor-causal dynamic occupancy.** Register that same moving prim as
  a transform-tracked target for both the MID-360-like ray caster and the
  D435i-like depth camera. SCAN receives only rendered scene observations and
  simulator-truth robot/sensor pose. Dynamic-object bounds, identity, schedule,
  or ground truth may be used for evidence classification but never for cloud
  injection, planner filtering, command generation, or robot steering.
- **R36 — Reactive avoidance and clearance.** Freeze a crossing that creates a
  time-space conflict with the nominal route. Record when the obstacle enters
  the corridor, sensor detections, occupancy/replan or emergency-stop events,
  every SCAN B-spline, commands, and physical poses. Acceptance requires a
  causally later trajectory response plus positive time-synchronized physical
  clearance and zero non-foot collision; no predictive-planning claim is made.
- **R37 — V7 evidence and preservation.** Keep all V6 files immutable. V7 uses
  a new dated evidence boundary containing motion identity, scene/sensor
  identities, raw and overlaid MP4s, dynamic and robot trajectories, plan
  records, contacts, metrics, thresholds, hashes, and local re-evaluation.
  Freeze thresholds after preflight and two same-input dry runs but before the
  final review candidate.
- **R38 — Bounded occupied-voxel freshness.** V7 may add one disabled-by-default
  SCAN map parameter that expires an occupied source voxel only after it has
  received no hit for a frozen number of complete cloud updates. Static
  geometry that remains observed must refresh continuously. The expiry must
  remove its paired inflation contribution, remain off for V1--V6, be unit
  tested, and be recorded as a V7 project adaptation rather than upstream
  dynamic prediction.
- **R39 — Bounded replan tracking catch-up.** V7 may use a separate controller
  parameter file with a frozen maximum tracking error no smaller than the
  measured safety-replan start mismatch and no larger than the value qualified
  by dry runs. A V7-only minimum catch-up command may clear the measured V12
  low-speed deadband, but applies only while returning to the received
  B-spline start and remains within the unchanged policy velocity bound. The
  controller still follows only the received SCAN B-spline; this change may
  not add a waypoint, robot pose write, or scripted turn.
- **R40 — Replan backpressure during catch-up.** While the controller reports
  a dedicated bounded start-catch-up state, SCAN may defer additional
  collision-triggered optimizer calls and continue processing pose/cloud
  callbacks. The broader execution-frozen signal used for trajectory-time and
  heading alignment must not suppress collision checking. Collision checking
  resumes as soon as strict tracking is restored. The catch-up command remains
  bounded and follows the received trajectory start; this is not permission to
  ignore a collision during heading or normal trajectory execution.
- **R41 — Official human identity.** V8 R2 references the NVIDIA Isaac Sim 5.1
  `male_adult_police_04` character and the official Isaac People Biped graph.
  Record the versioned URLs, extension/runtime versions, server
  metadata, available file hashes, and applicable NVIDIA asset-license boundary.
  Do not copy or redistribute the official character content into this repo.
- **R42 — Stable physical representation.** A hidden terrain-seated capsule
  under a dedicated kinematic rigid root owns collision, mass, pose scheduling,
  readback, sensor occupancy, and synchronized clearance. A separate visual root
  is registered by the official shoe sole. Both roots share schedule time, XY,
  and heading while retaining their explicit vertical datums. Visible limbs do
  not create unstable articulated collision. The capsule radius and total height
  are frozen before dry runs; collision-disabled viewport-only motion cannot
  satisfy V8.
- **R43 — Official animation and sensor-visible occupancy.** Crossing uses an
  official Isaac People Biped AnimationGraph pose after ControlRig retargeting
  to the exact 101-joint character skeleton; waiting and hold phases use the
  official graph's idle output. Because the People graph is incompatible with
  the pinned Direct-GPU process, this output is generated in a separate bounded
  process and replayed from a validated runtime cache. No local gait generator
  may animate the visible human. Runtime evidence must identify
  whether each sensor reads the deforming official mesh or a conservative
  co-moving sensor proxy; this distinction must be visible in the manifest and
  overlay. In either case, no truth points may be injected into SCAN.
- **R44 — V8 evidence and preservation.** Create a new dated V8 local/remote
  boundary. Preserve V7 unchanged, obtain two identical-input passing V8 dry
  runs, freeze new human-specific thresholds, then execute one uninterrupted
  review candidate. Copy back the generated USD, hashes, stage audit, raw and
  overlay videos, sensor/trajectory/contact traces, ROS bag, and acceptance
  reports before making any V8 claim.

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
- [x] **AC18 — V4 identity gate:** local and remote manifests reproduce the
  pinned forest commits, checkpoint, canonical/Isaac URDFs, observation/action
  contract, sensor frames, and runtime versions with matching hashes.
- [x] **AC19 — Forest geometry gate:** at least one route-relevant visible
  obstacle has an explicit physics collider and is included in both declared
  simulated sensor backends; a contact/raycast probe distinguishes it from the
  ground and visual-only vegetation.
- [x] **AC20 — Forest locomotion gate:** the unchanged V12 policy drives the
  articulated Lite3 through the frozen short command schedule with finite
  state, valid foot support, no hidden reset/teleport, and recorded collision
  outcome.
- [x] **AC21 — V4 evidence gate:** a directly openable MP4, raw metrics,
  command/action/contact trace, scene and robot identities, runtime log, and
  remote/local SHA-256 manifest are present in a new dated evidence directory.
- [x] **AC22 — V4 human review:** Dr Sun reviewed V4 and requested faster
  motion plus obstacle avoidance. V4 is retained as a rejected final candidate,
  not relabeled as accepted.
- [x] **AC23 — V4 change request recorded:** Dr Sun explicitly requested faster
  motion and obstacle avoidance; V4 remains immutable and is marked
  change-requested rather than accepted.
- [x] **AC24 — V5 terrain filter:** unit tests and runtime metrics show the
  planner cloud is derived only from raw point geometry, suppresses traversable
  sloped terrain, retains the direct-path tree, and causes no planner-origin
  occupancy error.
- [x] **AC25 — V5 speed:** SCAN and the controller share the frozen 0.50 m/s
  limit; the trace contains at least one forward command of 0.45 m/s or higher
  and a measured planar-speed response of at least 0.30 m/s without changing
  the V12 policy/controller contract.
- [x] **AC26 — V5 physical avoidance:** the direct path intersects the declared
  blocker, SCAN publishes at least two unique trajectories, and the physical
  root path maintains the frozen blocker clearance while producing a
  nontrivial lateral detour and zero non-foot collision.
- [x] **AC27 — V5 closed-loop result:** the articulated Lite3 reaches the fixed
  forest goal and stops within tolerance with finite policy state, support,
  advancing dual-sensor data, no hidden reset/teleport, no protocol/watchdog
  error, and no manual or scripted avoidance command.
- [x] **AC28 — V5 evidence:** two identical-input dry runs and one review
  candidate have complete local/remote hash parity, decoded MP4, ROS bag,
  planner log, command/action/contact trace, terrain/filter identity, and
  machine-readable acceptance report.
- [x] **AC29 — V5 human review:** Dr Sun reviewed V5 and requested a V6 with a
  1.0 m/s target, corrected rock/proxy or rock/terrain appearance, and visible
  planned-versus-actual trajectories. V5 is retained as change-requested, not
  accepted.
- [x] **AC30 — V6 speed:** all four forward-command boundaries equal 1.0 m/s;
  the trace contains a planner command of at least 0.90 m/s and the physical
  response during low-yaw high-command samples satisfies the threshold frozen
  before the final candidate, with no policy, collision, support, watchdog, or
  finite-state failure.
- [x] **AC31 — V6 geometry:** a runtime geometry report proves every reviewed
  rock's source visual is seated against sampled terrain without visible
  penetration, its collision/sensor proxy is registered and active, and no
  simplified proxy is visible through the final source visual.
- [x] **AC32 — V6 trajectory display:** the review video simultaneously shows
  a labeled sampled SCAN B-spline and labeled accumulated Isaac PhysX root
  path; both are reproducible from hashed raw records and synchronized to the
  displayed run.
- [x] **AC33 — V6 evidence:** two identical-input passing dry runs and one
  frozen candidate have complete local/remote hash parity, decoded raw and
  overlay MP4s, ROS bag, complete B-spline records, root trace, geometry audit,
  speed evidence, collision/goal outcome, and machine-readable acceptance.
- [x] **AC34 — V6 human-review disposition:** Dr Sun requested a V7 dynamic
  obstacle candidate. V6 remains immutable automated-pass evidence and is
  marked change-requested rather than accepted.
- [x] **AC35 — V7 moving-body and sensor gate:** runtime records prove one
  terrain-seated visible/collidable body follows the frozen crossing schedule,
  its actual pose advances as expected, and both simulated sensors observe the
  same moving prim at multiple distinct poses without injected points.
- [x] **AC36 — V7 reactive-planning gate:** the frozen nominal route and moving
  obstacle overlap in time and space; after live sensor detection SCAN replaces
  the active trajectory or invokes its emergency-stop path, with event timing
  and complete B-spline provenance showing the response is sensor-causal rather
  than scripted or predictive. The frozen occupied-voxel freshness window
  clears departed-object inflation without removing continuously observed
  static blockers, and the frozen tracking window permits the physical robot to
  catch up to a safety-replanned B-spline without changing its geometry.
- [x] **AC37 — V7 physical-result gate:** the unchanged V12 policy drives the
  articulated Lite3 to the goal or a declared safe stop while maintaining the
  frozen time-synchronized obstacle clearance, zero non-foot collision, finite
  state, valid support, advancing sensors, and no robot teleport or scripted
  avoidance command.
- [x] **AC38 — V7 evidence gate:** two identical-input passing dry runs and one
  frozen candidate have complete local/remote hash parity, decodable raw and
  overlay MP4s, ROS bag, obstacle commanded/readback trajectory, sensor-hit
  trace, map/replan events, SCAN paths, physical root path, contacts, and a
  machine-readable acceptance report.
- [ ] **AC39 — V7 human review:** Dr Sun watches the complete V7 overlay MP4
  and explicitly accepts or rejects obstacle motion and visibility, reactive
  avoidance, planned-versus-actual motion, speed, terrain appearance, and stop
  or goal behavior.
- [x] **AC40 — V8 R2 official asset gate:** runtime inspection proves the
  visible actor is NVIDIA's versioned Isaac Sim 5.1
  `male_adult_police_04`, records its source/version/license evidence, shows no
  procedural-human fallback, and proves the separate hidden collidable capsule
  shares schedule time, XY, and heading without appearing in RGB output.
- [x] **AC41 — V8 R2 official animation and sensor gate:** an official Isaac
  Biped-retargeted walk is visibly active during crossing and its idle output is
  active outside it; the cache proves exact 101-joint output and non-static
  walk/idle pose arrays. Both simulated sensors observe the co-moving capsule at
  multiple actor positions. Truth remains evidence-only and no points are
  injected into SCAN.
- [x] **AC42 — V8 R2 reactive physical result:** under the unchanged V7 schedule,
  planner/controller adaptations, policy, robot, forest, and speed boundary,
  SCAN produces a causally later response and the articulated Lite3 reaches
  the goal or declared safe stop with positive capsule clearance, zero non-foot
  collision, finite state, advancing sensors, and no scripted robot motion.
- [x] **AC43 — V8 R2 evidence gate:** one official-human visual preflight accepted
  by Dr Sun precedes two identical-input passing dry runs and one
  frozen review candidate have complete local/remote hash parity, a decodable
  raw MP4 and official-human overlay, asset manifest and stage audit, animation
  trace, dual-sensor observations, ROS bag, SCAN paths, physical root path,
  contacts, and machine-readable acceptance.
- [ ] **AC44 — V8 R2 human review:** Dr Sun watches the full V8 R2 raw and overlay
  videos and explicitly judges human recognizability, gait, sensor-causal
  avoidance, planned-versus-actual motion, terrain appearance, speed, clearance,
  and terminal behavior. Automated PASS cannot satisfy this criterion.
- [ ] **AC45 — Auxiliary voxel-video review:** one same-scenario run records
  nonempty raw and inflated SCAN occupancy topics plus the sliding-map bounds,
  body pose, and B-spline; a deterministic renderer produces a decodable,
  timestamped MP4 whose source hashes and frame metadata are copied locally.
  Dr Sun visually reviews the result; this auxiliary artifact does not modify
  AC40--AC44 or promote the upstream reproduction claim.
- [ ] **AC46 — Native RViz replay review:** the copied Foxy rosbag or a
  hash-linked standard-message replay preserves the complete raw and inflated
  PointCloud2 payloads, 0.05 m voxel resolution, sliding-map bounds, exact
  sampled SCAN path, and accumulated physical body path. RoboStack Humble RViz2
  on osx-arm64 renders the data with a recorded configuration and produces a
  directly decodable screen recording. Automated replay checks do not satisfy
  Dr Sun's visual decision.
- [ ] **AC47 — Official indoor scene visual gate:** Warehouse, Office, and
  Hospital are each loaded from their recorded Isaac Sim 5.1 USD URI on the
  5070 Ti. Resolver status, stage bounds, prim/collider counts, runtime log,
  raw multi-view PNGs, source hashes, and remote/local parity are preserved.
  This gate proves only scene loading and visual appearance.
- [ ] **AC48 — Lite3 scale-context gate:** the pinned Lite3 sensor-rig URDF is
  inserted through the recorded Isaac Lab importer path without replacing the
  source scene, and at least one raw view per scene shows robot scale and
  placement. A fixed-base visual preview cannot be promoted into articulated
  locomotion, collision, sensor, or navigation evidence.
- [ ] **AC49 — Indoor-scene human review:** Dr Sun reviews the Warehouse,
  Office, and Hospital previews and selects which scene, if any, should enter a
  separate collision/sensor/route qualification. Automated checks cannot make
  the selection.
- [ ] **AC50 — Office global-tour human review:** a locally synchronized H.264
  video contains actual moving-camera Isaac RGB output for every authored
  Office floor surface while composing all Office direct children except the
  separately declared city-background prim. Metadata records the source floor
  mesh evidence, per-floor bounds and visible prims, frame count, resolution,
  rate, and output hashes. Black frames, static-image animation, inventing a
  floor from stair height, and labeling a reception crop as global are
  forbidden. Dr Sun decides whether the visual tour is acceptable.
- [x] **AC51 — Office L0 physical-scene gate:** the official L0 floor, walls,
  doors, desks, tables, and other route-relevant source meshes have recorded
  collision coverage derived from their source geometry rather than loose
  hand-authored boxes. A stationary articulated Lite3 with the pinned sensor
  URDF maintains supported foot contact without non-foot contact, tunnelling,
  or interpenetration. Visual preview evidence cannot satisfy this gate.
- [x] **AC52 — Office Lite3/SCAN composition gate:** the pinned V12
  `model_149999` policy contract, Lite3 sensor-rig URDF, MID-360-like ray model,
  D435i-like depth model, Foxy TCP bridge, and SCAN planner are unchanged except
  for a separately hashed Office L0 scenario configuration. A route of at least
  20 m is planned from sensor-derived occupancy; scene truth may evaluate the
  run but may not steer the robot or populate SCAN.
- [x] **AC53 — Eight-pedestrian causal-obstacle gate:** eight NVIDIA official
  animated characters follow deterministic, source-floor-constrained routes at
  0.6--1.2 m/s. At least two cross the nominal Lite3 route while six provide
  background traffic. Each visible character has one co-moving conservative
  collision/sensor proxy, but character truth and route schedules remain
  evidence-only. Swept routes must pass static-scene and person-person
  intersection prechecks before the closed loop starts. Crossing endpoints
  must remain outside the combined robot/person envelope.
- [x] **AC54 — Office crowd repeatability gate:** two same-input closed-loop
  runs use the same Office, policy, planner, sensor, pedestrian, start/goal, and
  configuration hashes. Each run has zero physical collision, zero protocol or
  watchdog error, reaches within 0.25 m of the goal, records at least one causal
  SCAN trajectory replacement after a crossing pedestrian enters sensor view,
  and preserves planned versus physical trajectories plus per-person clearance.
  This is reactive moving-occupancy evidence, not predictive social navigation.
- [ ] **AC55 — Office crowd human review:** a locally synchronized video shows
  the articulated Lite3, all eight official pedestrians, planned trajectory,
  actual trajectory, detected dynamic occupancy, and replanning events in the
  official Office L0 scene. Dr Sun alone decides visual plausibility and whether
  the trial is acceptable for the project baseline.

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
- Multi-map, multi-seed, comparative benchmark, predictive dynamic planning,
  multi-agent intention modeling, or general dynamic-navigation claims beyond
  the single frozen V7/V8 crossing.
- Human pose estimation, pedestrian intention prediction, semantic person
  detection, social-navigation cost fields, general crowd simulation beyond
  the fixed eight-person Office trial, or claims about safe operation near real
  people.
