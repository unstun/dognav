# Implementation Plan: Foxy SCAN to Lite3 Isaac Closed Loop

> V2 implementation and automated verification completed on 2026-08-13. The
> first frozen run was preserved as a failure; after returning to the owning
> integration gates, two identical-input dry runs and
> `acceptance_v2_frozen` passed. Human review then reopened the task for V3:
> new sensor-rig URDF plus the V12 checkpoint, simulated MID-360, and simulated
> D435i. V1/V2 remain immutable evidence.

## Preconditions Before `task.py start`

- [x] Dr Sun reviews the final `prd.md`, `design.md`, and this plan and gives a
  fresh explicit implementation approval after that review.
- [x] The task remains in `planning`; no remote installation or implementation
  begins before approval.
- [x] Unrelated dirty paths and the active CAD child task are recorded and left
  untouched.

## Phase 0 — Activate and Freeze the Execution Boundary

- [x] Run the Trellis Phase 1.4 review gate, then start this existing task.
- [x] Load `trellis-before-dev` before the first implementation edit.
- [x] Create a task branch using the `codex/` prefix if the current repository
  policy permits it; record the base commit and dirty-path exclusions.
- [x] Create a local execution manifest naming the local source of truth,
  remote task root, sync direction, expected artifacts, and claim boundary.
- [x] Recheck the 5070 Ti OS/GPU/disk/Isaac/runtime state and the sibling
  `machine-dog` commit/worktree without modifying either.

**Rollback point:** no remote changes and no imported upstream source.

## Phase 1 — Pin SCAN and Build the Provenance Record

- [x] Acquire the selected `ros2-community` revision into
  `references/upstream/2026-08-13_scan-planner-ros2-community/` without local
  source edits.
- [x] Record URL, branch, commit, fetch time, recursive file hashes, root and
  per-package license evidence, original build/launch instructions, dependency
  graph, and selected Foxy package inventory.
- [x] Record the excluded Humble/Fortress/Go2 packages and why they are not part
  of this port.
- [x] Add a reproducible patch-generation method so every port difference can
  be reviewed against the untouched snapshot.

**Gate 1:** the snapshot identity and minimal package boundary are reviewable.

## Phase 2 — Establish the Isolated Foxy Runtime

- [x] Select an official or otherwise source-verifiable Ubuntu 20.04 / ROS 2
  Foxy image/root filesystem and pin its immutable digest.
- [x] If no runtime exists, perform the approved one-time container-runtime
  installation through an interactive privilege prompt. Do not echo, pipe,
  script, log, or persist credentials.
- [x] Bind any published TCP port to localhost only and mount only the
  task-owned workspace/evidence paths needed for the run.
- [x] Capture the host and container environment inventory, installed packages,
  image digest, compiler/CMake/Python/PCL/Eigen versions, and before/after host
  mutation record.
- [x] Prove a clean Foxy publisher/subscriber smoke test and persistent artifact
  write-back to the local-source workspace copy.

**Gate 2:** a reproducible Foxy runtime exists without native Foxy installation
on Ubuntu 24.04. If runtime installation cannot be completed safely, stop and
record the blocker.

## Phase 3 — Port and Test the SCAN Core

- [x] Create the Foxy overlay under `integration/scan_planner_foxy_ws/src/`
  from the selected package set, retaining notices and traceability.
- [x] Patch Humble-only build metadata/APIs minimally; remove Fortress/`ros_gz`
  dependencies from the selected execution graph.
- [x] Centralize topics, frame IDs, planner/map settings, controller bounds,
  rates, start/goal interface, and success tolerance in a reviewed config.
- [x] Add focused tests for message conversion, config loading, numeric
  validation, controller saturation, and deterministic node startup.
- [x] Build and test from a fresh Foxy workspace:

  ```bash
  colcon build --symlink-install --event-handlers console_direct+
  colcon test --event-handlers console_direct+
  colcon test-result --verbose
  ```

- [x] Launch the selected nodes with synthetic point-cloud/odometry input and
  confirm trajectory plus bounded `cmd_vel` output without Gazebo Fortress or
  `go2_kinematic_sim`.

**Gate 3:** AC3 passes and the complete port diff is attributable to Foxy
compatibility or task-owned integration.

## Phase 4 — Implement and Qualify TCP Protocol v1

- [x] Add the shared protocol schema/constants/test vectors, Foxy `rclpy`
  bridge, and Isaac-side standard-library TCP adapter under
  `integration/lite3_sim_bridge/`.
- [x] Implement separate telemetry and command streams, bounded length-prefixed
  reads, CRC32, sequence/timestamp handling, finite-value checks, reconnects,
  local-only endpoints, and fail-closed state transitions.
- [x] Convert `SENSOR_FRAME_V1` to synchronized PointCloud2/body/sensor odometry
  and convert Foxy Twist to clamped `CMD_VEL_V1`.
- [x] Add deterministic tests for full/partial/coalesced frames, corrupted CRC,
  bad version/type/flags, oversize lengths, invalid points/quaternions,
  sequence gaps, timestamp propagation, disconnect/reconnect, latest-wins
  behavior, saturation, and watchdog zeroing.
- [x] Run a local two-process loopback smoke with synthetic moving geometry and
  a command step schedule; preserve raw logs and machine-readable timing.

**Gate 4:** AC4 passes before any policy or planner is connected to the bridge.

## Phase 5 — Pin and Qualify the Lite3 Locomotion Payload

- [x] Inventory existing committed Lite3 velocity-policy candidates and their
  evidence without changing the dirty sibling worktree.
- [x] Select one candidate source commit, environment/config, robot asset, and
  checkpoint; record paths and SHA-256 hashes. Copy only the required immutable
  runtime payload into the task-owned remote directory.
- [x] Implement the task-owned Isaac adapter so the latest command is written
  to the live command tensor before policy observation/inference.
- [x] Run one fixed-seed environment with the safe
  zero/forward/lateral/yaw/zero command schedule and capture the full causal
  trace required by AC5.
- [x] Disconnect the command stream and verify the frozen watchdog forces zero
  command without a NaN, fall, or hidden reset.
- [x] If the first candidate fails, evaluate at most one other existing,
  immutable velocity-policy candidate with the same gate. Do not train or
  repair a checkpoint inside this task.

**Gate 5:** AC5 passes. Otherwise stop with candidate-specific evidence and do
not connect SCAN.

## Phase 6 — Qualify Simulated LiDAR and Truth Pose

- [x] Attach an RTX LiDAR when reliable in the pinned runtime; otherwise use a
  named Isaac ray-cast LiDAR and record the fidelity downgrade explicitly.
- [x] Define the nominal sensor extrinsic and all world/base/sensor frame
  conversions in versioned configuration; include their hash in each frame.
- [x] Verify point count, finite ratio, timestamp progression, expected ground
  and obstacle returns, scene occlusion response, pose-dependent changes, and
  PointCloud2/odometry synchronization through the Foxy bridge.
- [x] Freeze voxel/downsample settings, point cap, sensor rate, transform
  convention, and truth-pose label for the acceptance run.

**Gate 6:** AC6 passes. Static map points or unsynchronized pose data are not an
acceptable fallback.

## Phase 7 — Closed-Loop Integration and Dry Runs

- [x] Build one deterministic obstacle course with declared robot collision
  clearance, fixed start/goal, seed, and termination conditions.
- [x] Connect the full loop only after Gates 1–6 pass.
- [x] Run short dry runs to establish measured planner/sensor/policy/physics
  rates and bridge latency; fix correctness defects without relaxing the
  physical/sensor causal chain.
- [x] Freeze command bounds, watchdog, point cap/rate, latency and drop limits,
  goal tolerance, collision threshold, maximum duration, and reset policy in a
  signed-off acceptance config before the final run.
- [x] Confirm the telemetry can detect base teleportation, direct pose writes,
  manual mid-run commands, stale input, NaNs, collision, and resets.

**Rollback point:** revert only task-owned adapters/configs to the last passing
gate; never fall back to kinematic motion or map-truth sensing.

## Phase 8 — Run the Frozen Acceptance Scenario

- [x] Start raw log capture, ROS-side recording, metrics writer, and video
  capture before issuing the fixed goal.
- [x] Execute one uninterrupted run from the frozen start to goal/termination.
- [x] Record the complete causal path from planner trajectory through policy
  and PhysX back to sensor/pose feedback.
- [x] Evaluate AC7 and AC8 from machine-readable data, then visually inspect the
  actual MP4 for physical movement, obstacle interaction, contacts/support, and
  absence of hidden resets or teleportation.
- [x] If the gate fails, preserve the run unchanged, classify the failure, and
  return only to the owning earlier phase. Do not edit thresholds after seeing
  the result and call the same run accepted.

## Phase 9 — Sync, Verify, and Close

- [x] Copy all expected artifacts into the dated local experiment path and
  compare local/remote SHA-256 manifests.
- [x] Ensure the MP4 is a directly openable regular file and the raw logs,
  configs, patches, hashes, metrics, and ROS-side recording are complete.
- [x] Run repository tests, task validation, link/path checks, and
  `git diff --check`; review every changed path against task ownership.
- [x] Run `trellis-check`, resolve findings, and record the final evidence label
  without exceeding AC10.
- [x] Update project terminology/spec/state only for durable verified facts,
  then make one reviewed task commit. Do not stage the pre-existing unrelated
  research files or the CAD child task.
- [ ] Use the Trellis finish workflow only after Dr Sun completes human review
  and all success acceptance
  criteria pass. A stop-condition report leaves the integration claim
  incomplete and requests the next user-owned decision.

## Phase 10 — Freeze and Import the V3 Sensor Rig

- [x] Copy only the pinned canonical and Isaac-safe URDF bundle from the
  committed `machine-dog` source into a dated ignored runtime reference; record
  source commits, licences, all mesh hashes, topology, and mass/collision
  expectations without reading the dirty sibling worktree as runtime input.
- [x] Add a V3 asset override that changes only the V12 robot spawn path and
  fixed-joint setting; assert the checkpoint, observation, action, pose,
  actuator, timing, seed, and command contracts remain byte/value identical.
- [x] On the 5070 Ti, import one environment and record prim/link/joint/body,
  mass, collision, sensor-frame, and default-mass readback.

**Gate 10:** AC11 passes. Preserve any importer failure without falling back to
the legacy asset.

## Phase 11 — Bind and Qualify MID-360 and D435i

- [x] Probe the installed Isaac runtime for RTX LiDAR compatibility. Use it
  only if creation, attachment, output, teardown, and evidence capture pass;
  otherwise freeze the multi-mesh ray-cast backend and geometry-derived rig
  occlusion mask.
- [x] Bind the LiDAR to `mid360_scan_frame`; record FOV/range/rate/sampling,
  raw/finite/floor/obstacle/self-occlusion counts, timestamps, and pose change.
- [x] Bind the depth sensor to `d435i_depth_optical_frame`; record provisional
  intrinsics, resolution/range/rate, finite ratio, obstacle pixels, timestamp,
  pose change, and representative raw/visualized depth frames.
- [x] Add deterministic local tests for asset/config hashes, frame bindings,
  mask logic, depth metrics, invalid sensor data, and identity serialization.

**Gate 11:** AC13 and AC14 pass together. A visual sensor mesh without live
data, a TORSO-relative substitute, or a static-map image is a failure.

## Phase 12 — Qualify V12 on the New Physical Asset

- [x] Run the same fixed-seed zero/forward/lateral/yaw/zero schedule on the
  legacy V12 asset and the new rig asset with identical policy/control inputs.
- [x] Compare command visibility, observation, action, response direction,
  support, root height/attitude, contacts, non-foot collision, finite state,
  termination, and watchdog behavior without changing thresholds after either
  result.
- [x] Stop if the new rig fails; do not train, tune the controller, delete
  payload collision, or reuse the legacy-asset PASS as V3 evidence.

**Gate 12:** AC12 passes.

## Phase 13 — V3 Closed Loop and Frozen Acceptance

- [x] Run at least two identical-input dry runs with the new asset and both
  sensors active. SCAN consumes only the MID-360 point stream; D435i data is
  recorded concurrently.
- [x] Freeze a V3 acceptance config and run identity only after both dry runs
  pass without threshold changes.
- [x] Execute one uninterrupted formal V3 run with raw logs, ROS recording,
  dual-sensor metrics/depth samples, full causal telemetry, and a video that
  visibly shows the imported sensor rig.
- [x] Preserve any failed frozen V3 run and return to its owning gate.

**Gate 13:** AC15 passes.

## Phase 14 — V3 Evidence and Human Review

- [x] Copy expected artifacts back to a new local V3 evidence directory and
  verify local/remote hashes, structured data, video decode, depth samples,
  source/config identity, and task-owned diff.
- [x] Update the report so V2 remains baseline-only and V3 receives no stronger
  label than its direct evidence.
- [x] Run full Trellis/code/evidence checks, make a reviewed commit, set the
  task to `review`, and provide the V3 MP4 plus human-review checklist directly.
- [ ] Archive only after Dr Sun explicitly accepts V3.

## Phase 15 — V4 Forest Locomotion Preview

- [x] Preserve V1--V3 evidence and create a new dated V4 experiment directory
  naming the local source of truth, remote run root, expected files, and claim
  boundary.
- [x] Pin and verify `forest_gen` `v0.3.8`, STRIPE-kit, the V3 checkpoint,
  canonical/Isaac URDF bundle, policy/config source, and runtime identities.
- [x] Build a task-owned forest adapter that reuses the V3 policy/robot runtime,
  keeps upstream visual assets unchanged, instances visual-only vegetation,
  and adds separately named route-relevant trunk/rock collision and sensor
  proxies.
- [x] Run a static one-environment gate proving Lite3 topology/sensor frames,
  visual/collision/sensor agreement for a declared obstacle, finite sensor
  output, and absence of unexpected bodies or default mass.
- [x] Run the frozen zero/forward/yaw/zero V12 command sequence without
  training or tuning; record policy/actions, articulated motion, contacts,
  support, collisions, resets, termination, and performance.
- [x] Capture a directly viewable MP4, close simulation-time instrumentation
  before encoding/teardown, copy all artifacts back, and verify remote/local
  SHA-256 parity plus local decode and structured-data checks.
- [x] Run Trellis checks and return the video for Dr Sun's explicit human
  acceptance. Do not start a SCAN forest closed loop inside V4.

**Gate 15:** AC18--AC21 pass before the preview is called reproduced; AC22
remains unchecked until Dr Sun reviews the video.

## Phase 16 — Reopen From V4 Human Feedback

- [x] Record Dr Sun's request for faster motion and avoidance as a V4
  change-request decision without modifying V4 raw artifacts.
- [x] Freeze V5 as planner-driven avoidance, not a scripted turn: 0.50 m/s
  SCAN/controller limit, deterministic forest seed, direct-path tree, fixed
  start/goal, unchanged V12 checkpoint and sensor-rig hashes.
- [x] Return the task to `in_progress`, keep unrelated dirty paths excluded,
  and create a new dated local/remote V5 evidence boundary.

## Phase 17 — Implement the Forest Navigation Data Path

- [x] Add a tested geometry-only local-minimum terrain filter; reject any
  implementation that selects planner points from terrain truth, prim IDs,
  proxy bounds, or obstacle labels.
- [x] Add the opt-in `forest_gen_nav` layout while preserving V4
  `forest_gen`; place one shared visual/PhysX/LiDAR/depth tree proxy across the
  direct route and record its geometry.
- [x] Add a V5 planner config with the fixed goal and existing 0.50 m/s limit;
  make the launch and common runner accept explicit config/course inputs while
  preserving V3 defaults.
- [x] Extend machine-readable metrics and acceptance evaluation for raw versus
  planner point counts, terrain filtering, maximum forward command, measured
  planar speed, direct-line intersection, lateral detour, blocker clearance,
  and terrain-relative base clearance.
- [x] Run local Python/C++/launch/shell tests before remote synchronization.

## Phase 18 — Remote Dry Runs and Candidate

- [x] Create a task-owned V5 execution copy on the 5070 Ti, pin every source
  and binary hash, rebuild the changed Foxy workspace in the existing rootless
  Foxy container, and run an instrumentation preflight. Video remained active
  in the diagnostic because the first full run identified the combined
  sensor/render workload as the relevant transport stressor.
- [x] Preserve failures and fix only their owning layer. Do not reduce robot
  inflation, obstacle size, clearance, speed evidence, or collision thresholds
  after seeing a run.
- [x] Obtain two identical-input passing dry runs, compare terrain/config/input
  hashes, then freeze the candidate thresholds.
- [x] Run one uninterrupted video candidate with SCAN, ROS bag, dual sensors,
  V12 policy, PhysX contacts, and complete causal metrics active.

## Phase 19 — Sync, Check, and Human Review

- [x] Copy all V5 results and logs into the dated local bundle; verify structured
  data, depth array, full-video decode, ROS bag, binary identities, and exact
  remote/local hashes.
- [x] Run full Trellis checks and update the durable spec only for verified new
  contracts; commit only task-owned paths.
- [x] Set the task to `review` and deliver the actual V5 MP4 plus human
  checklist. Do not archive, start training, operate the robot, or call V5
  accepted before AC29.

**Gate 19:** AC24--AC28 pass before V5 is a review candidate; AC29 remains a
human-only decision.

## Phase 20 — Reopen From V5 Human Feedback

- [x] Record V5 as human change-requested and preserve every V5 artifact.
- [x] Create a new dated V6 local/remote evidence boundary and return the task
  to `in_progress`, excluding all unrelated dirty paths.
- [x] Reproduce the visible rock defect from V5 frames and add a runtime stage
  probe for source-visual bounds, proxy bounds, sampled support heights, and
  visibility before selecting the fix.
- [x] Freeze the V6 invariant set: V12 weights/contracts, sensor-rig URDFs,
  forest commits/seed, start/goal, and SCAN algorithm remain unchanged.

## Phase 21 — Implement V6 Speed, Geometry, and Trace Display

- [x] Add separate V6 planner/controller configs and explicit bridge/Isaac
  limits so all four forward ceilings are 1.0 m/s while acceleration stays
  0.5 m/s2; retain V5 defaults and files unchanged.
- [x] Implement and test terrain-support sampling plus source-visual/proxy
  registration. Remove simplified proxy geometry from final viewport
  rendering without removing collision or ray-cast participation.
- [x] Extend the Foxy monitor to persist complete B-spline values and timing;
  preserve the compact V5 summary contract.
- [x] Add a deterministic trajectory-overlay renderer and tests for B-spline
  sampling, time alignment, actual-root accumulation, colour/legend identity,
  video decode, and provenance sidecar hashes.
- [x] Extend acceptance for synchronized four-layer speed limits, high-command
  physical response, geometry seating, trajectory-record completeness, and
  raw/overlay video presence.
- [x] Run targeted Python, C++, launch, shell, and evidence tests locally.

## Phase 22 — Remote V6 Qualification and Candidate

- [x] Sync only task-owned V6 source/configuration to a new 5070 Ti execution
  copy and rebuild the changed Foxy workspace in the pinned container.
- [x] Run and preserve a geometry/overlay instrumentation preflight, followed
  by a short 1.0 m/s physical policy response preflight.
- [x] Run at least two identical-input forest dry runs; compare input and
  generated-geometry hashes and inspect raw plus overlay frames.
- [x] Freeze V6 thresholds before the final run, then execute one uninterrupted
  candidate with SCAN, ROS bag, dual sensors, policy/PhysX, raw video, complete
  path traces, and derived overlay video.

## Phase 23 — Sync, Check, Commit, and Human Review

- [x] Copy every V6 artifact locally and verify remote/local hashes, structured
  records, raw/overlay video decode, overlay provenance, geometry audit, and
  local acceptance re-evaluation.
- [x] Run `trellis-check`, update durable specs only for verified contracts,
  review the owned diff, and commit without staging unrelated research paths.
- [x] Set the task back to `review` and deliver the actual V6 overlay MP4 plus
  raw MP4 and human checklist. Do not archive or call V6 accepted before AC34.

**Gate 23:** AC30--AC33 pass before V6 is a review candidate; AC34 remains a
human-only decision.

## Phase 24 — Reopen From V6 Dynamic-Obstacle Feedback

- [x] Preserve every V6 artifact and record Dr Sun's dynamic-obstacle request
  as a human change request rather than accepting or relabeling V6.
- [x] Inspect the installed Isaac Lab transform-tracked ray-caster interface,
  SCAN occupancy clearing, and active-trajectory collision callback before
  freezing the V7 claim boundary.
- [x] Freeze V7 invariants: V12 weights/contracts, Lite3 sensor-rig URDF,
  forest source/seed/start/goal, 1.0 m/s limits, transport, and SCAN algorithms
  remain unchanged; V7 claims reactive rather than predictive avoidance.
- [x] Create a new dated V7 local/remote evidence boundary and return the task
  to `in_progress`, excluding all unrelated dirty paths.

## Phase 25 — Implement Dynamic Body, Sensing, and Evidence

- [x] Add and unit-test a deterministic command-relative
  wait/cross/hold/cross/park obstacle trajectory,
  terrain seating, schedule/readback comparison, and synchronized clearance.
- [x] Spawn one visible/collidable Isaac rigid body and register that same prim
  as a transform-tracked target for both simulated sensors; never write the
  robot root or inject obstacle points.
- [x] Record obstacle command/readback state, sensor hit counts, collision and
  clearance metrics, plan/replan timing, and immutable run identity.
- [x] Add a disabled-by-default, unit-tested occupied-source freshness window
  to the SCAN map and prove V7 clears departed-object inflation while retaining
  continuously observed static obstacles; keep V1--V6 behavior unchanged.
- [x] Qualify a V7-only controller tracking window against the measured
  safety-replan start mismatch without changing any speed, gain, policy,
  waypoint, or robot-root contract.
- [x] Defer collision-triggered optimizer calls only during controller-reported
  catch-up, then prove replanning resumes with current odometry and without a
  stale-start cascade.
- [x] Extend the review overlay and provenance sidecar with the dynamic path,
  current obstacle footprint, physical root, active SCAN plan, and clearance.
- [x] Extend acceptance and tests for motion, dual sensing, time-space conflict,
  causal SCAN response, physical clearance, goal/safe stop, video, and hashes.

## Phase 26 — Remote V7 Qualification and Candidate

- [x] Sync only task-owned V7 source/configuration to the 5070 Ti execution
  copy and rebuild changed components in their pinned runtimes.
- [x] Run a short dynamic-motion/dual-sensor preflight, then a causal crossing
  preflight; preserve failures and tune only the declared obstacle schedule.
- [x] Run two identical-input full dry runs and compare input, scene, obstacle,
  sensor, trajectory, and outcome evidence before freezing thresholds.
- [x] Freeze numerical acceptance thresholds and execute one uninterrupted V7
  review candidate with SCAN, ROS bag, dual sensors, policy/PhysX, contacts,
  raw video, and synchronized review overlay.

## Phase 27 — Sync, Check, Commit, and Human Review

- [x] Copy every V7 artifact locally and verify remote/local hashes, video
  decode, structured records, overlay provenance, and local acceptance parity.
- [x] Run `trellis-check`, review only task-owned changes, and commit without
  staging unrelated research paths.
- [x] Set the task to `review` and deliver the directly openable V7 overlay plus
  raw MP4 and human checklist. Do not archive or call V7 accepted before AC39.

**Gate 27:** AC35--AC38 pass before V7 is a review candidate; AC39 remains a
human-only decision.

## Planned Validation Matrix

| Layer | Required evidence | Failure response |
|---|---|---|
| Provenance | immutable snapshot + hashes + license/dependency record | stop import |
| Foxy runtime | pinned Ubuntu 20.04/Foxy identity + smoke | stop; no native Foxy |
| SCAN port | clean build, tests, synthetic trajectory/cmd | return to Phase 3 |
| TCP bridge | protocol unit/fuzz-like cases + loopback timing | return to Phase 4 |
| Locomotion | external command causal trace + contacts + watchdog | try one immutable fallback, then stop |
| Perception | scene-rendered cloud + synchronized truth pose | fix adapter/sensor; never use map truth |
| Closed loop | frozen goal run + metrics + MP4 | classify and return to owning gate |
| Evidence sync | local/remote hash parity + owned diff review | do not report completion |

## Known Risky Changes and Containment

- **Host package installation:** requires privilege and changes the 5070 Ti;
  capture before/after package state. Removal is not automatic.
- **Foxy API backport:** may alter behavior; keep the upstream snapshot
  unchanged and review every patch.
- **Policy suitability:** existing evidence may prove contact support but not
  velocity tracking; keep this as a hard preflight, not an assumption.
- **Sensor fidelity/performance:** RTX LiDAR may exceed the stable runtime
  budget; ray-cast LiDAR is allowed only with an explicit fidelity label and
  must still pass scene/occlusion tests.
- **TCP head-of-line/staleness:** use separate streams, bounded payloads,
  latest-command semantics, measured thresholds, and watchdog zeroing.
- **Remote-only drift:** all implementation originates locally and all evidence
  returns locally with hash parity before any claim.
