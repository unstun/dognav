# Quality Guidelines

> Code quality standards for navigation integration and evidence-producing runtimes.

---

## Overview

Navigation integration crosses binary transport, ROS messages, simulator state,
and evaluation artifacts. A passing unit test at one layer is not enough: the
serialized value must be checked at the next consumer and its physical effect
must be checked at runtime.

## Forbidden Patterns

- Passing network-order numeric payload bytes directly to a host-native ROS or
  PCL message. Convert byte order explicitly and test known float values.
- Classifying a simulated sensor hit only by a loose bounding box when another
  surface can occupy the same projection. Require a discriminating condition
  and retain raw hit counts.
- Treating sensor configuration as proof that every named mesh is in the actual
  ray-cast acceleration structure. Inspect runtime mesh-load evidence and prove
  non-ground returns.
- Relaxing planner collision thresholds to hide malformed clouds or frame
  errors.
- Promoting a transport, sensor, planner, or policy preflight into a closed-loop
  validation claim.

## Required Patterns

- Include frame, unit, numeric encoding, byte order, timestamp, and ownership in
  every cross-process sensor contract.
- Hash perception preprocessing settings into the run identity. Keep raw and
  filtered counts so filtering remains auditable.
- Fail closed on command drift, malformed payloads, non-finite values, stale
  commands, disconnects, collisions, and resets.
- Freeze acceptance thresholds after dry runs and before the acceptance run.
- Preserve failed runs unchanged and distinguish instrumentation failures from
  algorithm failures.

## Testing Requirements

- Protocol tests cover framing, partial reads, CRC, limits, timestamps,
  sequences, invalid numeric data, reconnects, saturation, and watchdog stop.
- Numeric boundary tests verify the exact bytes consumed downstream, not only
  encode/decode symmetry inside one module.
- Sensor gates distinguish traversable-floor returns from obstacle-surface
  returns and prove pose-dependent geometry.
- Full integration records planner output, commands, policy observation,
  physical motion and contacts, rendered sensing, and feedback in one run.

## Code Review Checklist

- Does each claim identify `surveyed`, `reproduced`, `integrated`, or
  `validated` evidence?
- Is every binary or frame conversion explicit and covered downstream?
- Can ground, robot self-returns, or stale frames masquerade as obstacles?
- Does a physical obstacle appear to both sensing and collision systems?
- Are source, checkpoint, config, logs, metrics, ROS recording, and video
  synchronized locally and hash-verified?

## Scenario: Preserve the Synchronized Bridge Root After Environment Activation

### 1. Scope / Trigger

Use this contract when a remote experiment driver activates conda, RoboStack,
ROS, or another environment before running bridge-dependent postprocessors.
Activation can rewrite `PYTHONPATH`; a historical run root may still contain an
importable but stale bridge and silently invalidate same-run evidence.

### 2. Signatures

```text
BRIDGE_ROOT=<hash-checked synchronized bridge package root>
RUN_ROOT=<historical experiment root; artifacts only>
PYTHONPATH="$BRIDGE_ROOT${PYTHONPATH:+:$PYTHONPATH}"
```

### 3. Contracts

- Resolve and hash-check `BRIDGE_ROOT` against the canonical local source before
  launch. `RUN_ROOT` is an artifact namespace and must not supply importable
  bridge code.
- After every environment activation, prepend the same `BRIDGE_ROOT` again;
  do not reconstruct a package path from `RUN_ROOT`.
- Record the effective bridge path and source hash with the run inputs. A
  postprocessor import must resolve under `BRIDGE_ROOT` before it evaluates
  runtime evidence.
- A stale-import failure is an instrumentation failure. Preserve the run and
  its failed audit; use a new run ID after repairing the driver.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Environment activation removes or reorders `PYTHONPATH` | Re-prepend the pinned `BRIDGE_ROOT` |
| Imported bridge path is outside `BRIDGE_ROOT` | Fail before postprocessing |
| Local and remote bridge hashes differ | Stop before remote execution |
| Stale bridge produces a failed audit | Preserve FAIL; do not relabel or overwrite the run |

### 5. Good / Base / Bad Cases

- **Good:** the driver syncs one bridge root, verifies its hash, activates the
  environment, re-prepends that root, and records the effective import path.
- **Base:** a clean image-installed package may be used only when its installed
  hash is the explicitly pinned execution source.
- **Bad:** activate conda and prepend `$RUN_ROOT/integration/...`; an older
  module imports successfully and yields a plausible but false audit failure.

### 6. Tests Required

- Statically assert every post-activation `PYTHONPATH` export uses
  `BRIDGE_ROOT` and that the historical `$RUN_ROOT/integration/...` expression
  is absent.
- In the remote preflight, import the bridge module and assert its resolved path
  lies below `BRIDGE_ROOT`; compare the synchronized source hash before launch.
- Preserve one fixture showing that a stale module would fail the current audit
  instead of silently accepting its result.

### 7. Wrong vs Correct

#### Wrong

```bash
source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
export PYTHONPATH="$RUN_ROOT/integration/lite3_sim_bridge${PYTHONPATH:+:$PYTHONPATH}"
```

#### Correct

```bash
source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
export PYTHONPATH="$BRIDGE_ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -c 'import lite3_sim_bridge; print(lite3_sim_bridge.__file__)'
```

## Scenario: Articulated Locomotion Follows a Perception-Replanned Trajectory

### 1. Scope / Trigger

Use this contract when a local planner advances a time-parameterized trajectory
for a policy-controlled articulated robot, especially when the occupancy map
is built from surface-only LiDAR returns. A kinematic follower's wall-clock
assumptions do not transfer automatically to a locomotion policy.

### 2. Signatures

- Trajectory progress decision:

  ```cpp
  TrajectoryProgressDecision decideTrajectoryProgress(
      double current_time,
      double dt,
      double duration,
      const Eigen::Vector2d &current_position,
      const Eigen::Vector2d &candidate_position,
      double max_tracking_error);
  ```

- Occlusion shadow projection:

  ```cpp
  std::vector<Eigen::Vector3d> occlusionShadowPoints(
      const Eigen::Vector3d &sensor_position,
      const Eigen::Vector3d &hit_position,
      double shadow_length,
      double resolution);
  ```

- Scenario parameters:

  ```yaml
  grid_map.double_cylinder_radius: <metres>
  grid_map.double_cylinder_offset: <metres>
  grid_map.occlusion_shadow_length: <metres, 0 disables>
  fsm.periodic_replan_enabled: <boolean>
  closed_loop_controller.max_tracking_error: <metres>
  ```

### 3. Contracts

- Evaluate trajectory progress against the candidate point at `current_time +
  dt`. If its planar distance from measured body pose exceeds
  `max_tracking_error`, keep the current trajectory time and publish the frozen
  state to the planner; continue commanding toward the current trajectory
  point rather than jumping ahead.
- Match planner and controller speed limits to the velocity-policy response
  demonstrated by the qualification gate. Transport saturation may be wider,
  but the trajectory generator and follower must share the accepted limit.
- Inflate physical obstacle hits by the declared robot proxy. When a sensor
  initially exposes only a surface, optionally mark points behind the hit along
  the same physical ray at voxel resolution; do not manufacture points in
  front of the hit or use scene-truth obstacle bounds as planner input.
- If distance-only periodic replanning is disabled, a separately timed safety
  callback must continue checking the active trajectory and must replan or
  fail closed when new occupancy invalidates it.
- Stop live command and telemetry transport at the simulation-time boundary
  before video encoding or slow simulator teardown. Post-run packaging must
  not consume queued commands or alter live transport statistics.
- Once trajectory time reaches its duration and measured pose first enters the
  declared finish tolerance, latch zero command until a new trajectory arrives.
  Do not let post-goal physical drift reopen a completed trajectory and create
  low-speed endpoint hunting.
- A formal run records hashes for the acceptance file, scenario configs,
  relevant source, executed binaries/libraries, container image, checkpoint,
  and policy source. Preserve every failed frozen run.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Candidate trajectory point exceeds tracking-error bound | Freeze trajectory time; do not skip ahead |
| Non-finite or non-positive shadow length/resolution | Disable shadow projection or reject configuration before runtime |
| Sensor origin equals hit point | Return no shadow points |
| Active trajectory intersects new inflated occupancy | Safety callback replans; imminent failure triggers emergency stop |
| Replacement candidate fails while active trajectory is still safe | Keep the active trajectory; never promote the failed candidate |
| Command frame is stale during live simulation | Reject it and fail closed |
| Simulation stepping has ended | Close transport before packaging; shutdown backlog is not a live protocol error |
| Frozen run fails collision, planning, transport, or goal gate | Preserve it unchanged and return to the owning phase |

### 5. Good / Base / Bad Cases

- **Good:** policy-qualified speed, measured-pose time freeze, conservative
  surface occlusion, event-driven safety replanning, zero collision, and an
  input hash manifest.
- **Base:** kinematic simulation may advance by trajectory time directly, but
  it cannot be promoted into the articulated physical-simulation claim.
- **Bad:** the desired trajectory is collision-free while the slower robot cuts
  the corner; the evaluator is then weakened to hide the contact.

### 6. Tests Required

- Unit-test the exact captured corner-cut positions: a candidate more than the
  tracking bound away must freeze, while a near candidate advances and clamps
  at duration.
- Unit-test the terminal latch: it remains false before trajectory duration or
  outside tolerance, becomes true at the first in-tolerance endpoint sample,
  and remains true after later pose drift until a new trajectory resets it.
- Unit-test shadow sample count, first/last sample position, disabled values,
  and degenerate rays.
- Run the full fixed-course loop at least twice with identical input hashes
  before a new formal acceptance run after a non-deterministic planning fix.
- Assert zero planner failures, zero origin-occupancy errors, zero protocol
  errors, zero watchdog events, physical detour, no non-foot collision, stopped
  command, and goal tolerance.
- Compare local and remote hashes for raw metrics, ROS bag, logs, MP4, configs,
  source, binaries/libraries, and image identity.

### 7. Wrong vs Correct

#### Wrong

```cpp
trajectory_time += wall_clock_dt;
```

```text
LiDAR surface hit -> mark one surface voxel -> treat all occluded volume free
```

#### Correct

```cpp
const auto progress = decideTrajectoryProgress(
    trajectory_time, dt, duration, measured_xy, candidate_xy,
    max_tracking_error);
trajectory_time = progress.next_time;
```

```text
physical LiDAR hit -> optional bounded shadow at voxel resolution
                   -> physical robot-envelope inflation
                   -> independently timed trajectory safety check
```

## Scenario: Preview A Large Official Isaac USD Scene

### 1. Scope / Trigger

Use this contract before selecting an official Warehouse, Office, Hospital, or
other composite USD as a navigation scene. A source URI resolving and a single
attractive image do not establish that the complete stage is practical on the
target GPU or physically valid for a quadruped.

### 2. Signatures

```text
capture_official_scene.py
  --scene <catalog key>
  --output-dir <new run directory>
  [--robot-asset <pinned URDF> --robot-position X Y Z]
  [--hide-prim <source prim>]
  [--crop-center X Y --crop-radius R --subset-reference]
  [--clay]
  [--camera-eye X Y Z --camera-target X Y Z]
```

Each output directory contains raw PNGs and `capture_metadata.json` with the
source URI, runtime bounds, stage counts, source-composition mode, hidden and
selected source prims, camera poses, optional robot identity, file hashes, and
claim boundary.

### 3. Contracts

- Keep the official scene URI immutable and record the exact Isaac asset-pack
  version. Do not copy NVIDIA scene content into the repository.
- Use a newly created offscreen camera from a recorded eye/target pose. A source
  Camera prim may be inspected for pose, but must not be assumed to produce an
  operational Replicator render product.
- If the source stage packages distant context with the navigation scene,
  inspect the hierarchy before rendering. A local subset may reference direct
  source prims individually; it must be labeled a subset and may not be called
  the complete scene.
- Treat spatial overlap as a candidate selector, not an allowlist. A large
  backdrop or instanced context prim can overlap the crop even when it is not
  part of the navigable interior. Record and review every selected direct-child
  path, support explicit exclusions, and keep visual background composition
  separate from later collision and route composition.
- A complete-source first-frame timeout does not prove that source materials
  are unusable. Retry a bounded, source-prim subset with source materials before
  falling back to clay, and retain the complete-source timeout as negative
  evidence.
- For a multi-level global tour, derive every declared floor from authored
  floor-surface bounds. A staircase, elevator shaft, wall, or overall stage
  height does not establish another floor. Record floor-surface count, XY
  bounds, floor Z, and visible source prims for every video segment.
- If ceilings or inactive levels are hidden to expose a floor plan, record the
  visibility rule and label the result a per-floor global visualization. It is
  not an unchanged complete-scene camera view or collision-completeness proof.
- Clay material overrides change appearance only. Record them and never use a
  clay preview as source-material evidence.
- A fixed-base Lite3 is a scale reference only. It is not articulated
  locomotion, contact, sensor, or planner evidence.
- Bound every first-frame attempt. Preserve timeouts rather than repeatedly
  extending the limit until an image appears.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Official URI does not resolve | Stop before stage creation |
| Full scene exceeds the frozen first-frame limit | Preserve the log; classify runtime preparation as failed |
| Root bounds are dominated by distant context | Inspect children; hide or source-reference a recorded local subset |
| Spatial crop retains a giant background/context prim | Record the selected path, explicitly exclude or separately classify it, and rerender |
| Stair height suggests a level with no authored floor surface | Reject the level; preserve the failed attempt and rebuild the floor inventory |
| Upper floors or ceilings occlude a global floor-plan view | Hide only the recorded inactive-level/ceiling prims and publish per-floor visibility metadata |
| Direct source Camera render product produces no frame | Recreate an offscreen camera from a recorded pose |
| Camera is inside a wall, roof, or prop | Preserve the view as rejected and use a new recorded pose |
| Key obstacle is visible but collider coverage is unknown | Keep the result visual-only; open a collision gate separately |
| Optional robot is fixed-base | Label visual scale reference; prohibit locomotion claims |

### 5. Good / Base / Bad Cases

- **Good:** complete source Warehouse, source materials, fixed-base Lite3 scale
  view, decoded PNGs, exact URI, stage inventory, bounded runtime, and hashes.
- **Base:** a source-prim Office or Hospital subset with clay materials can be
  used for geometry triage when the complete source scene times out.
- **Bad:** rendering an unbounded composite stage until it eventually responds,
  hiding the timeout, and reporting the resulting image as an Isaac Lab
  navigation integration.

### 6. Tests Required

- Unit-test the scene catalog, URI ordering, bounds validation, and deterministic
  camera derivation.
- Decode every selected PNG and verify byte size and SHA-256 against metadata.
- Assert that subset runs record every selected and hidden source prim and that
  complete-source and subset labels cannot be confused.
- Assert that declared excluded context prims are absent from
  `selected_source_prims`; inspect the selected list before accepting crop
  bounds as a local navigation region.
- Exercise source-material subset rendering independently of the
  complete-source result; a complete timeout must not force clay mode.
- Unit-test floor assignment and camera interpolation. Runtime metadata must
  prove each declared floor has at least one source floor mesh and positive XY
  extent.
- Decode the complete video, verify codec/rate/resolution/frame count and
  local/remote hashes, run bounded black-frame detection, and review a regular
  contact sheet before presenting a global-tour candidate.
- Assert the optional URDF hash, spawn position, and fixed-base label.
- Preserve failed logs for viewport capture, complete-scene timeout, bad camera,
  and over-large crop attempts.
- Before navigation, run separate collision, articulated locomotion, sensor,
  and route gates; preview success cannot satisfy them.

### 7. Wrong vs Correct

#### Wrong

```text
office.usd resolved -> screenshot exists -> Office is ready for Lite3 navigation
```

#### Correct

```text
official URI -> bounded hierarchy inspection -> bounded visual preview
             -> human scene selection
             -> collision/contact gate -> sensor gate -> route/SCAN gate
```

```text
complete source timeout -> bounded source-material subset -> human appearance check
                        -> clay only if the source-material subset also fails
```

```text
stage Z extent or stairs -> assume four floors -> global-tour claim
```

```text
source floor-mesh bounds -> admit B1/L0/L1 only -> per-floor visibility record
                         -> decoded moving-camera video -> human review
```

## Scenario: Compose a Pinned Locomotion Policy with a Sensor-Rig URDF

### 1. Scope / Trigger

Use this contract when an existing policy-qualified robot runtime is moved to a
new URDF that adds payload, collision geometry, fixed sensor frames, or live
simulated sensors. A source URDF hash or successful import alone does not prove
that the policy contract, physical composition, or sensor data path is valid.

### 2. Signatures

- V3 asset override:

  ```text
  --robot-asset <Isaac-safe URDF>
  --canonical-robot-asset <canonical URDF>
  ```

- Required runtime evidence:

  ```text
  runtime_composition.json
  run_identity.json
  sensor_metrics.jsonl
  depth_metrics.jsonl
  qualification_report.json
  ```

- Sensor-frame contract:

  ```text
  MID-360-like point stream -> mid360_scan_frame -> SCAN
  D435i-like depth stream   -> d435i_depth_optical_frame -> evidence only
  ```

### 3. Contracts

- Treat the policy/controller and robot asset as separate immutable identities.
  Hash the checkpoint, policy source, observation dimension, action ordering,
  default pose, actuator configuration, timing, seed, command schedule,
  canonical URDF, Isaac-safe URDF, and referenced meshes.
- Change only the spawn asset and fixed-joint import setting for the
  single-variable qualification. Reject accidental changes to the 450-value
  observation, 12-action contract, command limits, or watchdog.
- Preserve fixed sensor-frame joints and read back bodies, joints, masses,
  inertias, collision prims, and named sensor frames from the instantiated USD
  stage. Explicit tiny inertials used only for fixed frame bodies must be
  declared; silent importer default mass is forbidden.
- Bind sensors to the imported named frames. A task-relative transform or a
  visible sensor mesh without live data does not satisfy the contract.
- For rig self-occlusion, ray-cast against the moving visual surface that
  represents the blocker. Broad collision proxies may be used for physics but
  must not silently replace visual geometry in the optical mask. A self hit
  blocks the environmental ray; it must not be removed and allowed to pass
  through the robot.
- Record sensor backend, FOV, range, rate, sample grid/resolution, transforms,
  filtering, self-occlusion counts, finite/nonempty counts, timestamps, and
  pose-dependent change. Declare simulator-truth pose explicitly.
- When a hardware-specific RTX profile is absent or its creation/output/
  teardown lifecycle does not complete, preserve the probe and use a named
  geometric fallback. Do not substitute another vendor profile or claim
  hardware parity.
- Run at least two identical-input passing dry runs before freezing a new
  acceptance configuration. Preserve earlier failures and do not relax a
  physical or sensor threshold after observing the formal result.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Canonical or Isaac URDF hash differs | Stop before simulator import |
| Policy/checkpoint/observation/action invariant differs | Reject the comparison as multi-variable |
| Fixed sensor frame is merged or absent at runtime | Fail asset qualification |
| Runtime body receives undeclared default mass | Fail asset qualification |
| Collision-proxy self mask removes all environmental rays | Preserve failed preflight; switch only to declared visual-surface occlusion |
| Sensor stream is empty, non-finite, static in time, or task-relative | Fail sensor qualification |
| D435i intrinsics lack depth-camera calibration evidence | Label provisional; do not claim hardware parity |
| RTX profile or teardown probe is incomplete | Reject RTX backend for the declared run and record the geometric fallback |
| A/B locomotion candidate terminates, loses support, or hits non-foot geometry | Stop before closed-loop integration; do not train or retune inside the gate |
| Local/remote artifact hashes differ | Do not promote or report the remote result |

### 5. Good / Base / Bad Cases

- **Good:** pinned policy and two URDF hashes, runtime topology/mass/collision
  readback, same-input old/new asset qualification, live data at both imported
  sensor frames, visual-surface self-occlusion, two passing dry runs, frozen
  gate, and local/remote evidence parity.
- **Base:** a legacy asset with a task-mounted ray caster can remain a clearly
  labeled baseline, but it cannot satisfy a sensor-rig acceptance criterion.
- **Bad:** show a new URDF in a viewer while the closed loop still spawns the
  old asset, publishes a hard-coded torso-relative scan, or treats a static
  depth image as a live D435i stream.

### 6. Tests Required

- Unit-test exact checkpoint/URDF/config hashes, required frame names, topology
  counts, mass tolerance, absence of missing/default-mass bodies, sensor
  settings, depth artifact hashes, invalid data, and identity serialization.
- Run the same zero/forward/lateral/yaw/zero/watchdog schedule on old and new
  assets with identical policy inputs. Assert finite state, response direction,
  support, no termination, no non-foot collision, and watchdog zeroing.
- Assert LiDAR and depth timestamps advance, data are finite and nonempty,
  scene obstacle evidence appears, poses change, and self-occlusion counts are
  recorded.
- Re-evaluate the copied formal artifacts locally with the frozen config,
  decode the MP4, parse JSON/JSONL/YAML, load the depth array, inspect ROS bag
  payload presence, and compare local/remote hashes.
- Leave the human acceptance criterion unchecked until the named reviewer
  records an explicit decision after watching the full video.

### 7. Wrong vs Correct

#### Wrong

```text
new URDF exists -> reuse old runtime PASS -> call the sensor rig validated
```

```text
collision proxy blocks ray -> delete self hit -> ray reaches obstacle behind robot
```

#### Correct

```text
pin policy + canonical URDF + Isaac URDF
  -> runtime readback
  -> same-input locomotion A/B
  -> live dual-sensor gate
  -> two passing dry runs
  -> frozen formal run
  -> local parity check
  -> human review
```

```text
visual rig surface blocks ray -> record self-occlusion -> no environmental hit
```

## Scenario: Qualify a Pinned Locomotion Policy on Procedural Forest Terrain

### 1. Scope / Trigger

Use this scenario when an already-qualified locomotion policy and robot asset
are exercised on imported or procedurally generated terrain, especially when
the run must also prove live simulated LiDAR/depth response and deliver a video
for human review. This scenario is an experiment gate, not a training or
planner-integration gate.

### 2. Signatures

- The runtime must expose an explicit forest course and immutable run inputs:

  ```text
  --course forest_gen
  --seed <integer>
  --checkpoint <pinned file>
  --canonical-urdf <pinned file>
  --isaac-urdf <pinned file>
  --output-dir <run-owned directory>
  [--record-video]
  ```

- The run bundle must contain at least:

  ```text
  qualification_report.json
  run_identity.json
  runtime_composition.json
  policy_metrics.jsonl
  sensor_metrics.jsonl
  depth_metrics.jsonl
  output_sha256.txt
  forest_lite3_v12.mp4       # when video is requested
  ```

  The generated terrain identity and static proxy audit may be embedded in
  `run_identity.json`, `runtime_composition.json`, and
  `qualification_report.json`; they do not require duplicate sidecar files.

- The launcher exit contract is independent of simulator shutdown behavior:

  ```text
  missing qualification_report.json -> exit 90
  qualification_report.status != PASS -> exit 91
  PASS report and complete artifacts -> exit 0
  ```

### 3. Contracts

- Verify the forest-source commits, checkpoint hash, canonical URDF hash, and
  Isaac-safe URDF hash before starting the simulator. Record the exact policy,
  robot, terrain, command schedule, sensor, physics, and seed identities.
- Do not infer determinism from an upstream `seed` parameter. Inspect every
  random-number source used by terrain and asset population. Either route the
  declared seed into all of them or freeze and compare the generated geometry
  hash across identical-input runs.
- Normalize upstream mesh visual types only when required by the simulator
  importer. Preserve the source vertices and faces, and record the resulting
  mesh hash so a rendering compatibility conversion cannot silently change the
  terrain.
- Every route-relevant tree or rock needs a visible source asset plus a
  registered collision/sensor proxy targeted by both the MID-360-like and
  D435i-like sensor queries. The simplified proxy may be hidden in the final
  review render only when runtime evidence records the visual/proxy pairing,
  bounds, transform, collision API, sensor targets, and hidden render state. A
  decorative asset beside an unrelated invisible collider does not satisfy
  this contract.
- Seat irregular source meshes from an actual low-surface datum or real mesh
  support vertices. A full axis-aligned box corner may contain no geometry and
  can make a non-penetrating asset visibly float on sloped terrain. Preserve
  the failed placement, record the chosen support points and clearance, and
  keep human appearance review separate from the numerical contact audit.
- Bind the policy command terrain key to the declared course without changing
  the pinned observation/action contract. The recorded command tensor, not
  only the requested schedule, is the evidence that zero/forward/yaw/stop
  reached the policy.
- Treat the machine-readable qualification report as the launcher truth
  source. Some simulator shutdown paths can swallow the Python process return
  code, so a shell exit code alone must never promote a run.
- Keep automated qualification and human visual acceptance separate. A
  decoded video can pass instrumentation while an occluding camera makes it
  unusable for review; preserve that run as superseded and record a new camera
  run without changing the experiment inputs.
- Preserve failed attempts, copy complete artifacts back to the local source
  of truth, and prove local/remote hash parity before reporting a run as ready
  for review.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Forest source commit, checkpoint, or URDF hash differs | Stop before simulator import |
| Identical seed produces a different terrain geometry hash | Fail reproducibility; seed all hidden RNGs or freeze the generated asset |
| Upstream visual mesh types cannot be concatenated by the importer | Preserve failure; normalize visuals without changing vertices/faces |
| Forest course is absent from the policy command-terrain mapping | Fail before policy inference; add an explicit unchanged-contract binding |
| Source visual is absent, or paired proxy lacks collision or either sensor target | Fail static geometry qualification |
| Full-box seating passes numerically but the source mesh visibly floats | Preserve the preflight; switch to a recorded real-surface support datum and repeat human review |
| Qualification report is missing after simulator exit | Launcher exits 90 even if the simulator process returned zero |
| Qualification report status is not `PASS` | Launcher exits 91 and preserves the report and logs |
| Video cannot be decoded or the robot is materially occluded | Keep automated result; mark video superseded and leave human review pending |
| Local/remote artifact hashes differ | Do not present the local bundle as the executed evidence |

### 5. Good / Base / Bad Cases

- **Good:** pinned identities, repeated identical terrain hash, visible source
  assets with registered collidable/dual-sensor-targeted proxies, real-surface
  seating evidence, recorded policy response on uneven ground, launcher report
  enforcement, complete local hash parity, decoded unobstructed video, and a
  separate pending human decision.
- **Base:** a deterministic flat or obstacle course can validate the policy and
  sensors, but it cannot be promoted as forest-terrain evidence.
- **Bad:** launch a photorealistic forest backdrop with a flat invisible floor,
  let LiDAR query different geometry from physics, trust process exit zero, or
  call an occluded video human-approved.

### 6. Tests Required

- Unit-test forest report evaluation, missing/static proxy rejection, identity
  serialization, command scheduling, and the launcher exit mapping.
- Run at least two identical-input terrain generations and assert the complete
  mesh hash is identical. Record the seed and all upstream commit hashes.
- Inspect the instantiated stage and assert terrain plus every route-relevant
  source visual is visible; assert its paired proxy has the declared render
  state, collision API, transform/bounds agreement, and both sensor targets.
- Execute the pinned policy on the terrain and assert finite state/action,
  scheduled command visibility, nontrivial displacement, terrain-height
  variation, support/contact bounds, and no hidden reset or termination.
- Assert LiDAR/depth timestamps advance, outputs are finite and nonempty,
  obstacle returns exist, and readings change with pose.
- Decode the full video, inspect representative frames, parse JSON/JSONL,
  verify the recorded terrain identity, and compare remote/local SHA-256
  manifests.
- Leave human acceptance unchecked until the named reviewer watches the full
  video and records a decision.

### 7. Wrong vs Correct

#### Wrong

```text
upstream seed set + simulator exit 0 + MP4 exists -> forest run validated
```

```text
photorealistic tree visual + separate invisible box + sensor-only mesh -> same obstacle
```

#### Correct

```text
pin policy + URDFs + forest commits
  -> seed every RNG / compare terrain hash
  -> inspect visible-collision-sensor geometry
  -> run recorded policy schedule
  -> enforce qualification_report.status
  -> copy and hash-check artifacts
  -> decode unobstructed video
  -> human review remains a separate decision
```

```text
visible source asset + registered proxy -> PhysX collision + LiDAR target + depth target
```

## Scenario: Coalesce a Buffered Command Backlog Without Relaxing Freshness

### 1. Scope / Trigger

Use this contract when a simulator or another non-real-time producer can pause
wall-clock command consumption while physics is also paused. A local TCP sender
may continue placing 50 Hz command frames in the socket buffer. This is a
latest-wins backlog case, not permission to widen the real-robot watchdog.

### 2. Signatures

- Atomic state update:

  ```python
  LatestCommandState.update_batch(
      updates: Sequence[Tuple[CommandV1, int, int, int]]
  ) -> CommandSnapshot
  # tuple fields: command, sequence, source_timestamp_ns, received_monotonic_ns
  ```

- Transport evidence:

  ```python
  TransportStats.coalesced_frames: int
  ```

- The receiver may collect at most 256 complete command frames that are
  already readable with a zero-timeout socket readiness check. It must not wait
  for a future frame to make a stale latest frame appear fresh.

### 3. Contracts

- Decode and validate every complete buffered frame. Observe every command
  sequence in increasing order before applying state, so intentional
  coalescing is not reported as packet loss.
- Intermediate source-stale commands are never applied. Apply only the newest
  command, and only when that newest source timestamp satisfies the unchanged
  `max_source_age_ns` and future-skew limits.
- A non-increasing sequence, malformed payload, non-finite value, future-skewed
  timestamp, or stale newest command rejects the whole batch through the
  existing fail-closed path. Validation must be atomic: a rejected batch may
  not partially advance the state sequence.
- Keep `timeout_ns` and `max_source_age_ns` at the scenario's previously
  qualified values. Record `coalesced_frames` separately from true sequence
  gaps, watchdog events, protocol errors, and reconnects.
- The formal run must hash both Isaac-side and Foxy-side protocol, transport,
  and command-state sources. Both process copies must be byte-identical.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Stale intermediates followed by a fresh latest frame | Observe all sequences; apply only latest; increment `coalesced_frames` |
| Newest buffered frame is stale | Reject batch and fail closed |
| Any frame has future skew or invalid numeric data | Reject batch and fail closed |
| Duplicate or decreasing sequence occurs inside batch | Reject atomically; retain prior sequence/state |
| Sequence is missing from the buffered batch | Count a real sequence gap |
| More than 256 frames are immediately buffered | Process a bounded batch; never allocate an unbounded queue |
| Formal run reports watchdog, protocol error, or reconnect | Preserve failure and return to transport diagnosis |

### 5. Good / Base / Bad Cases

- **Good:** a 275 ms simulator sensor synchronization leaves several valid
  frames buffered; the receiver validates the batch, applies the fresh latest
  command, reports bounded coalescing, and records zero gaps/watchdogs/errors.
- **Base:** a single fresh command uses `update()`, which delegates to the same
  one-element atomic batch contract.
- **Bad:** disconnect on the first stale intermediate frame, discard fresher
  frames behind it, then increase the watchdog until the acceptance report
  turns green.

### 6. Tests Required

- Send one combined TCP write containing multiple stale command frames followed
  by a fresh latest frame. Assert the latest value is active, every sequence is
  observed, `coalesced_frames` equals the skipped intermediate count, and gaps,
  watchdog events, and protocol errors remain zero.
- Unit-test that a stale newest frame and a future-skewed frame are rejected.
- Unit-test that an internal duplicate sequence leaves the prior state and gap
  count unchanged.
- Re-run the full sensor/render workload with the original source-age and
  watchdog values. Require zero reconnects, gaps, watchdog events, and protocol
  errors, and record the bounded coalesced-frame count in acceptance evidence.

### 7. Wrong vs Correct

#### Wrong

```python
frame = recv_frame(connection)
state.update(decoded(frame))  # oldest buffered frame can be stale
# On error: disconnect and lose fresher frames already queued behind it.
```

```text
stale backlog observed -> increase watchdog/source-age threshold
```

#### Correct

```python
frames = receive_complete_frames_already_buffered(limit=256)
updates = [decode_and_validate(frame) for frame in frames]
state.update_batch(updates)  # observes all; applies only fresh latest
```

```text
stale intermediates + fresh latest -> bounded atomic coalesce
stale latest / malformed batch     -> unchanged fail-closed path
```

## Scenario: React to a Moving Obstacle with a Policy-Controlled Robot

### 1. Scope / Trigger

Use this contract when a moving simulator body updates a SCAN-style occupancy
map and can invalidate the active B-spline while an articulated locomotion
policy lags or starts behind a replacement trajectory. It is a reactive
moving-occupancy contract, not velocity prediction or intention modeling.

### 2. Signatures

```yaml
grid_map.occupied_decay_updates: <complete cloud updates; 0 disables>
closed_loop_controller.max_tracking_error: <strict metres>
closed_loop_controller.replan_catchup_max_error: <fail-closed metres>
closed_loop_controller.replan_catchup_min_speed: <catch-up-only m/s>
```

```text
planning/go2_execution_frozen  # trajectory-time alignment only
planning/go2_catchup_active    # collision-replan backpressure only
```

```cpp
TrajectoryCatchupState classifyTrajectoryCatchup(
    double start_error, double strict_error, double maximum_catchup_error);
Eigen::Vector2d boundedCatchupVelocity(
    const Eigen::Vector2d &position_error, double gain,
    double minimum_speed, double maximum_speed);
bool shouldDeferCollisionReplan(bool catchup_active);
```

### 3. Contracts

- A dynamic body is one visible, collidable, terrain-seated prim tracked by
  every declared simulated sensor. A command-relative schedule may begin only
  after the first accepted nonzero robot command so simulator startup latency
  cannot decide the collision outcome.
- SCAN receives rendered point geometry only. Dynamic-body truth may classify
  sensor hits, compare scheduled/readback poses, compute synchronized
  clearance, and draw evidence; it may not inject or remove planner points,
  generate a trajectory, or steer the robot.
- Occupied-source freshness is disabled by default. When enabled, each
  occupied source voxel records the most recent complete cloud update that hit
  it. Expiry removes the source occupancy and its reference-counted inflation
  contribution only after the full configured age. Continuously observed
  static geometry refreshes its age.
- A replacement trajectory inside the strict tracking window starts normal
  B-spline execution. A larger mismatch up to the maximum enters bounded
  position-only catch-up with B-spline time frozen. A larger mismatch is
  rejected and stopped. A minimum catch-up speed may clear a measured policy
  deadband, but applies only in `CATCHUP` and remains below the unchanged
  policy maximum.
- `go2_execution_frozen` may freeze SCAN trajectory time for heading, tracking,
  or catch-up alignment. It must never suppress collision checking by itself.
  Only the separately published `go2_catchup_active` state may defer another
  optimizer call, and collision checking resumes immediately on `TRACKING` or
  `REJECTED`.
- Goal success for a locomotion policy requires a continuous in-tolerance
  stopped window. Later zero-command stance drift is recorded and bounded
  separately; shortening a run to hide drift is forbidden.
- Freeze thresholds only after two passing same-source/config dry runs. A
  post-candidate safety review can supersede an automated PASS; preserve it and
  requalify the changed code before naming another review candidate.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Freshness parameter is zero | Preserve legacy occupancy behavior |
| Occupied source is hit again | Refresh age; retain occupancy and inflation |
| Source exceeds full update age | Remove its occupancy and one paired inflation contribution |
| Replacement start error is within strict bound | Track normally; catch-up inactive |
| Start error is between strict and maximum bounds | Freeze B-spline time; command only toward the received start |
| Catch-up proportional command falls inside the measured policy deadband | Apply the frozen catch-up-only minimum norm |
| Start error exceeds maximum | Reject, publish zero command, keep collision checking active |
| Heading or ordinary tracking freezes execution time | Keep collision checking active |
| Catch-up is active | Defer only another collision optimizer call; continue pose/cloud callbacks |
| Dynamic body contacts a non-foot link or triggers reset | Preserve FAIL; do not retime or shrink the obstacle after the frozen run |
| Robot reaches and stops, then drifts | Report stable-arrival event and bounded later drift separately |

### 5. Good / Base / Bad Cases

- **Good:** command-relative collidable body, transform-tracked dual sensing,
  rendered-only planner input, default-off freshness, bounded catch-up with a
  dedicated backpressure state, live collision checks outside catch-up, two
  same-input dry runs, frozen candidate, local hash parity, and human review.
- **Base:** a static blocker can validate the geometric closed loop, but cannot
  support a moving-obstacle claim.
- **Bad:** animate a collision-disabled visual, classify truth bounds into the
  planner cloud, reuse a broad execution-frozen signal to suppress collision
  checks, widen normal tracking to absorb mismatch, or rerun a startup-timed
  crossing until one attempt happens not to collide.

### 6. Tests Required

- Unit-test wait/cross/hold/cross/park schedule boundaries, invalid dimensions,
  hold fraction, terrain seating, pose readback, and signed circle clearance.
- Unit-test occupied-age boundary behavior with disabled, unobserved,
  refreshed, exact-age, and expired sources; integration evidence must retain
  a static blocker after departed-body cells expire.
- Unit-test `TRACKING`, `CATCHUP`, and `REJECTED`; prove the minimum catch-up
  speed clears a small request, maximum speed still saturates, and zero error
  stays zero.
- Assert collision replanning defers for `CATCHUP` only, not tracking, heading
  alignment, ordinary time freeze, or rejected trajectory state.
- Run a physical dry run that actually exercises a large bounded mismatch and
  another same-input run through normal tracking before freezing.
- In the frozen run, assert command-relative trigger evidence, all motion
  phases, dual-sensor multi-pose detections, a causally later SCAN plan,
  positive synchronized clearance, zero non-foot collision, stable goal stop,
  bounded later drift, decoded raw/overlay videos, ROS bag integrity, and
  local/remote SHA-256 parity.

### 7. Wrong vs Correct

#### Wrong

```cpp
if (go2_execution_frozen)
  return;  // also hides collisions during heading and ordinary tracking freeze
```

```text
dynamic truth bounds -> synthetic planner points -> apparent replan
```

#### Correct

```cpp
if (go2_catchup_active)
  return;  // optimizer backpressure only during bounded start catch-up
// heading/tracking/rejected states still execute collision checking
```

```text
command-relative PhysX body -> transform-tracked sensor hits -> SCAN occupancy
  -> reactive B-spline -> bounded catch-up if needed -> articulated motion
  -> synchronized clearance/contact evidence
```

## Scenario: Preview a Run-Start Constant-Velocity Pedestrian

### 1. Scope / Trigger

Use this contract only for an auxiliary visual trial where the pedestrian must
move independently of the robot command. It is not the frozen reactive-obstacle
acceptance schedule.

### 2. Signatures

```text
--dynamic-obstacle-schedule-trigger first_nonzero_body_command|run_start
SCAN_DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER=first_nonzero_body_command|run_start
```

### 3. Contracts

- `first_nonzero_body_command` remains the default and the only accepted mode
  for the frozen V7/V8 reactive-obstacle candidate.
- `run_start` initializes the pedestrian schedule immediately before the
  closed-loop stepping loop, independently of the received robot command.
- An immediate constant-velocity preview sets wait and hold to zero and makes
  the endpoint far enough that the actor does not park on the robot route
  during the rendered interval.
- Run identity, effective input, and per-step metrics record the trigger mode.
  A `run_start` preview must not produce or consume an acceptance report.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Trigger value is unknown | Reject before Isaac startup |
| `run_start` is used on a non-dynamic course | Reject before Isaac startup |
| First pedestrian motion occurs while robot command is zero | Record as expected independent-motion evidence |
| Crossing speed or lateral coordinate varies | Reject the constant-velocity claim |
| Short endpoint makes the person park in the robot route | Preserve as a collision negative; extend the preview route rather than hiding the contact |
| Acceptance is requested with `run_start` | Reject the result as outside the frozen contract |

### 5. Good / Base / Bad Cases

- **Good:** explicit `run_start`, zero wait/hold, constant recorded straight-line
  speed, long endpoint, zero contact, local evidence, and human-only review.
- **Base:** command-relative triggering remains the accepted reactive crossing.
- **Bad:** silently change the default trigger, stop the actor in the robot
  route, or report a run-start preview as the frozen avoidance candidate.

### 6. Tests Required

- Unit-test both trigger identities and rejection of unknown values.
- Assert the first nonzero pedestrian velocity precedes the first nonzero robot
  command, all moving samples have the declared speed, the transverse coordinate
  is constant, the longitudinal coordinate is monotonic, and hold/park counts
  are zero for the rendered interval.
- Preserve a collision-producing short-endpoint run when it informed the final
  route, and assert the selected preview has zero non-foot contact and positive
  synchronized clearance.

### 7. Wrong vs Correct

#### Wrong

```text
run_start + short route -> person parks in front of Lite3 -> collision hidden
```

#### Correct

```text
run_start + zero wait/hold + extended straight route
  -> constant pedestrian motion -> explicit non-acceptance visual preview
```

## Scenario: Replace a Dynamic Primitive with an Official Animated Human

### 1. Scope / Trigger

Use this contract when a previously qualified cylinder or box is replaced by a
ready-made vendor human asset while keeping the same reactive planner,
schedule, policy, robot, sensors, and physical-clearance claim. A recognizable
render alone is insufficient: the surfaces seen by planning must be
commensurate with the physical collision envelope.

### 2. Signatures

```python
def expand_isaac_env_regex_ns(prim_expr: str) -> str: ...
```

```text
visible asset: versioned official Isaac character URL under a visual-only root
animation: official Biped AnimationGraph retarget output, cached outside Direct GPU
physical proxy: one hidden capsule under a separate kinematic root
registration: common schedule time/XY/heading with explicit vertical datums
sensor contract: conservative co-moving capsule proxy
```

### 3. Contracts

- Pin the official asset URL and runtime version. Record source metadata,
  readable hashes, extension versions, license boundary, collision path, and
  animation identity. Never vendor or redistribute restricted vendor content.
- Keep the collision capsule hidden but collidable. Register its dedicated root
  and the visual root to the same schedule time, XY, and heading; compare the
  capsule-centre and shoe-sole vertical datums instead of equating root Z.
- Use the official Biped AnimationGraph and its ControlRig retarget output for
  visible gait. If Direct GPU cannot host the graph, generate a run-owned cache
  in a separate bounded Isaac process, validate exact joint order and non-static
  poses, and replay it without the graph. Do not implement a local procedural gait.
- The rendered body surface must be commensurate with the declared capsule at
  the sensor-facing planes. Compare early-route rendered hit counts and physical
  clearance against the primitive baseline. A sparse cosmetic body inside a
  broad collision capsule is a sensor/physics mismatch, not a planner failure.
- Normalize `{ENV_REGEX_NS}` to `/World/envs/env_.*` before comparing declared
  target expressions with Isaac's runtime target records.
- Human part identity, truth pose, capsule bounds, and gait angles are evidence
  only. SCAN receives rendered geometry; no semantic label, truth point,
  predicted velocity, or scripted avoidance command may enter planning.
- Preserve a collision-producing geometry run. Fix the owning representation
  layer, re-run a no-contact preflight and two same-input full dry runs, then
  freeze a new human-asset hash and acceptance file before a review candidate.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Official asset URL/version or readable hash differs | Stop or fail acceptance before promoting the run |
| Official character or animation fails to load | Fail the visual preflight |
| Capsule is visible, non-collidable, or registration error exceeds tolerance | Fail the physics gate |
| Cache joint order differs from the official character skeleton | Fail before scene startup |
| Walk or idle cache is static or contains invalid quaternions | Fail the visual preflight |
| A visible part lacks transform tracking in either sensor | Fail the sensor gate |
| Runtime target uses expanded environment regex | Normalize then compare exact expressions |
| Local procedural gait drives the visible human | Reject as out of scope |
| Visible surface is too sparse for its collision envelope | Preserve collision/clearance failure; enlarge or correct the rendered body |
| Human truth is used to add/remove planner points or steer | Reject the run as non-causal |
| Automated candidate passes but video is unreviewed | Keep task and manifest at human-review pending |

### 5. Good / Base / Bad Cases

- **Good:** versioned official animated human, hidden stable capsule, audited
  dual-sensor occupancy, comparable sensing/physics
  envelopes, positive clearance, frozen candidate, and pending human review.
- **Base:** the original cylinder remains a valid reactive-obstacle baseline but
  cannot satisfy human recognizability or gait evidence.
- **Bad:** draw a person around the old cylinder while sensors still target only
  the cylinder, or use a thin visible mannequin inside a broad capsule and
  blame SCAN after the robot contacts the unseen envelope.

### 6. Tests Required

- Unit-test official asset selection, phase-to-animation state, invalid phase,
  and environment-regex expansion.
- Assert the official asset/animation identity, one hidden collision prim,
  initialized synchronized roots, and no visible primitive fallback.
- Assert the declared official-mesh or proxy sensor targets are present in both
  runtime target lists and detected at multiple actor poses.
- Record early-route human hit counts, synchronized physical clearance, non-foot
  contact, causally later SCAN trajectories, goal stop, and overlay identity.
- Require a no-contact preflight, two same-effective-input full passes, one
  frozen run, local acceptance parity, ROS bag integrity, MP4 decode, and
  local/remote SHA-256 parity.

### 7. Wrong vs Correct

#### Wrong

```text
unverified downloaded model + broad hidden capsule
  -> sparse sensor returns -> late replan -> collision with unseen envelope
```

```python
expected = "{ENV_REGEX_NS}/DynamicObstacle/Visual/Head"
assert expected in runtime_targets  # Isaac has already expanded the token
```

#### Correct

```text
visible body commensurate with physical capsule
  -> transform-tracked rendered hits -> SCAN occupancy -> physical clearance
```

```python
expected = expand_isaac_env_regex_ns(
    "{ENV_REGEX_NS}/DynamicObstacle/Visual/Head"
)
assert expected in runtime_targets
```

## Scenario: Start Preset Navigation Only After Occupancy Is Ready

### 1. Scope / Trigger

Use this contract whenever SCAN preset-waypoint mode starts automatically from
simulated odometry and point-cloud streams. The first odometry callback may run
before the map has processed its first cloud; renderer or sensor workload can
change that ordering without changing any frozen experiment input.

### 2. Signatures

```cpp
bool GridMap::hasOccupancyObservation();
```

```cpp
if (navi_mode_ == NAVI_MODE::PRESET_TARGET && !preset_started_ &&
    planner_manager_->grid_map_->hasOccupancyObservation()) {
  preset_started_ = true;
  planGlobalTrajbyGivenWps();
}
```

### 3. Contracts

- `hasOccupancyObservation()` becomes true only after at least one processed
  occupancy update, not merely after cloud receipt, sensor pose, or odometry.
- Preset mode may record odometry and publish its robot envelope while waiting,
  but it must not create or publish a trajectory from an empty map.
- The readiness gate must not inject points, delay the dynamic actor schedule,
  alter planner/controller limits, or script robot motion.
- Log both the waiting state and the transition that starts preset planning so
  the launch order is auditable from the run evidence.
- After this race is fixed, preserve the collision-producing run and obtain a
  no-contact preflight plus two identical-input full passes before promotion.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Odometry arrives before any processed occupancy update | Keep preset mode unstarted and command zero |
| First occupancy update completes | Start the preset target exactly once |
| A rendered-load change alters callback timing | Inputs and behavior remain valid; no empty-map plan |
| Readiness never arrives | Remain fail-closed and fail the bounded run |
| Frozen collision run already exists | Preserve it and document the causal readiness fix |

### 5. Good / Base / Bad Cases

- **Good:** odometry is live, one occupancy update completes, the preset plan
  starts once, and later dynamic occupancy causes safety replanning.
- **Base:** manual goal mode may remain human-triggered after map inspection;
  it does not prove automatic preset readiness.
- **Bad:** start from the first odometry callback and rely on thread timing or
  renderer speed to make a cloud win the race.

### 6. Tests Required

- Build and run the `plan_env` and `scan_planner` test suites after changing
  the readiness API or preset start condition.
- Runtime logs must contain the wait and start messages in order, one initial
  plan only after readiness, and a causally later safety replan when the moving
  obstacle invalidates that plan.
- Require positive physical clearance, zero non-foot collision, goal or safe
  stop, and two passing identical-effective-input full runs.

### 7. Wrong vs Correct

#### Wrong

```cpp
have_odom_ = true;
if (!preset_started_) planGlobalTrajbyGivenWps();
```

#### Correct

```cpp
have_odom_ = true;
if (!preset_started_ && grid_map->hasOccupancyObservation()) {
  preset_started_ = true;
  planGlobalTrajbyGivenWps();
}
```

## Scenario: Office L0 Crowd Simulation and Long-Route Waypoint Sequencing

### 1. Scope / Trigger

Use this contract when deploying the SCAN planner in complex indoor architectural
USD scenes (such as Office L0) with long routes (>20 m) and multiple moving pedestrians.
Visual floor geometry in USD assets does not guarantee collision support; long routes
cannot rely on single-shot global planning across occluded indoor corridors; and dynamic
crowd obstacles require strict swept-route clearances and map-version gated replanning.

### 2. Signatures

- Preflight route and crowd contract:

  ```python
  def routes_from_preflight(payload: Mapping[str, object]) -> tuple[OfficePedestrianRoute, ...]
  def pairwise_clearance_precheck(routes: Sequence[OfficePedestrianRoute], duration_s: float, dt_s: float) -> dict
  ```

- Physics wrapper and floor qualification:

  ```text
  office_l0_physics_wrapper01.usda (triangle-mesh collision API on source floor/wall prims)
  office_l0_floor_drop02.json (static ball-drop and robot-support qualification)
  ```

- Planner sparse waypoint sequencing:

  ```yaml
  fsm.navi_mode: 2
  fsm.waypoints: [-11.625, 10.125, 0.85, -8.375, 10.125, 0.85, -8.375, 6.375, 0.85, -8.375, -0.625, 0.85]
  fsm.planning_horizon: 8.0
  grid_map.sliding_map_size_x: 16.0
  grid_map.sliding_map_size_y: 16.0
  ```

- Acceptance and repeatability interfaces:

  ```text
  office_crowd_acceptance.py --run-dir RUN --config CONFIG \
    --route-preflight ROUTE --planner-config PLANNER --overlay-video MP4
  office_crowd_repeatability.py --run-a RUN_A --run-b RUN_B \
    --acceptance-config CONFIG --route-preflight ROUTE --planner-config PLANNER
  ```

### 3. Contracts

- **Visual Floors Are Not Collision Proof**: Authored indoor USD visual meshes
  often lack PhysX collision APIs or contain non-collidable display surfaces.
  Every traversable floor surface must be qualified via explicit triangle-mesh
  physics wrappers and multi-point drop tests before robot placement.
- **TerrainImporter Raycast Target Caching**: In scenes with thousands of source
  prims, ray-cast sensor backends must cache the filtered static mesh acceleration
  structure at startup rather than querying the full scene graph per frame.
- **Sparse Waypoint Sequencing for Long Routes**: Dense global paths must never
  be sent to the local controller or masquerade as planned trajectories. AABB
  preflight only validates reachability and provides sparse (~7 m) intermediate
  waypoint goals; SCAN must generate all runtime local B-spline trajectories from
  sliding-map occupancy and truth pose feedback.
- **Map-Version Gated Replan Retries**: When moving obstacles temporarily block
  corridor transitions, A* search failures must trigger bounded retries with updated
  sliding-map occupancy rather than stale-start cascades or immediate aborts.
- **Pedestrian Route Margins**: All crossing and background pedestrian endpoints
  and trajectories must maintain verified static clearance from walls/furniture
  and pairwise clearance from each other, ensuring crossing endpoints remain outside
  the robot envelope.
- **Phase-Conditioned Pedestrian Motion**: A rendered walk cycle is permitted only
  while the scheduled root has nonzero planar velocity. Crossing actors use
  `single_pass` and idle at their endpoints; only background actors may use
  `ping_pong`, with a positive idle/turnaround hold between directions. Repeating
  every route blindly is forbidden because a crossing actor can re-enter the robot
  corridor after the original safety preflight window.
- **Sensor-Causal Replanning**: A reactive replan requires the same named person
  to be visible in both LiDAR and depth evidence, to approach the remaining
  continuous active B-spline, to have an actually captured SCAN inflated-occupancy
  sample near its position, and to be followed by a same-target B-spline whose
  geometry changes by the declared threshold. Ground-truth person circles are
  evaluation overlays only and must be labeled as such.
- **Simulator-Time Alignment**: Under sub-real-time simulation, map ROS event
  receipt time to simulator time by bracketing body-pose receipts and interpolating
  their simulator stamps. Wall-clock distance is not a valid sub-second causal
  tolerance. Record the bracketing simulator-time span and reject events whose
  mapping uncertainty exceeds the frozen limit.
- **Same-Input Repeatability**: Hash the effective acceptance, route, and planner
  inputs for each run. Compare a normalized run identity that excludes only the
  run ID, output paths, and identity's own derived hash. Two reports that merely
  share a scenario name are not same-input evidence.
- **Remote Copy Parity**: The local bridge source, Isaac execution copy, and Foxy
  workspace copy must have matching source hashes before a formal run. Rebuilding
  only one remote copy does not establish which monitor or bridge actually ran.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Floor visual mesh lacks collision API | Generate physics wrapper with triangle-mesh collider; verify drop test |
| Dense AABB preflight path used as command | Reject; use sparse waypoints only with SCAN B-spline generation |
| Crossing pedestrian enters active corridor | SCAN updates sliding occupancy and replans/slows reactively |
| Replan fails temporarily during occupancy shift | Keep active safe trajectory or retry on next map version; do not abort |
| Person truth is near a plan but no captured SCAN occupancy is near the person | Do not count a causal replan |
| Event receipt and body pose are aligned only in wall time | Recompute using bracketed simulator stamps or fail the causal gate |
| Effective input or normalized identity hash differs between repeats | Fail the repeatability gate |
| Isaac and Foxy execution copies differ from local source | Stop, resync both copies, rebuild, and record hashes |
| Robot-person conservative clearance < 0.15 m | Fail automated acceptance gate |
| Watchdog events > 0 or non-foot contact > 75 N | Fail automated acceptance gate |
| Walk animation is active while root velocity is zero | Fail pedestrian-motion fidelity; preserve the run |
| A crossing actor reverses into the robot corridor | Fail the schedule/safety preflight; create a new run ID |

### 5. Good / Base / Bad Cases

- **Good:** triangle-mesh qualified floor wrapper, sparse waypoint sequencing into
  SCAN, live sliding-map B-splines, 8 animated pedestrians observed via LiDAR/depth,
  positive clearance, zero non-foot collisions, and two same-input passing runs.
- **Base:** static-obstacle corridor navigation without moving pedestrians.
- **Bad:** feeding precomputed A* waypoints directly into the locomotion controller
  or claiming social navigation without sensor-causal evidence.

### 6. Tests Required

- Assert the route preflight, SCAN planner YAML, and acceptance config contain
  exactly the same ordered sparse waypoints.
- Unit-test per-person LiDAR/depth counts, rate-limited capture of
  `/grid_map/occupancy_inflate`, remaining continuous B-spline distance, and
  same-target geometric-difference calculation.
- Use adversarial causal fixtures: truth-only proximity, sensor-only detection,
  stale occupancy, a different target, and an unchanged replacement must all fail.
- Test simulator-time interpolation with deliberately slow wall-clock receipts;
  the mapped simulator stamp must remain correct and its bracketing simulator
  span must control acceptance.
- Assert minimum simulator duration, timestamp advancement, maximum physical
  step displacement, command bounds, cloud nonempty fraction, terminal command
  and speed stop windows, video frame count, and collision/watchdog gates.
- Run two complete closed loops, then assert identical effective-input and
  normalized-identity hashes, independent goal/collision/clearance success, and
  at least one causal replacement in each run.
- Compare SHA-256 for local source, both remote execution copies, configs,
  reports, raw videos, and review overlays before updating the task criterion.
- For a repeating crowd preview, assert eight named actors, root-moving samples
  cover at least 50% of actor-samples, some root motion exists during at least
  95% of the timeline, and both walk-while-stationary and idle-while-moving
  fractions are at most 1%. Re-run conservative robot/person and pairwise swept
  clearance across the complete requested duration.

### 7. Wrong vs Correct

#### Wrong

```text
person ground-truth pose near sampled polyline + later trajectory publication
  -> call it pedestrian-caused avoidance
```

```text
same scenario label + two PASS reports -> call inputs identical
```

```text
play every walk clip continuously + ping-pong every route
  -> stationary foot cycling and crossing-person corridor re-entry
```

#### Correct

```text
named LiDAR/depth detection
  -> named person approaches remaining continuous active B-spline
  -> captured SCAN inflated occupancy is near that person
  -> same-target later B-spline changes geometry
  -> count one sensor-causal reactive replacement
```

```text
hash effective configs + normalize only run/output identity fields
  -> compare hashes
  -> require both runs to pass independently
```

```text
crossing routes: single pass -> endpoint idle
background routes: forward walk -> idle turn -> reverse walk -> idle turn
  -> phase-conditioned clip follows scheduled root velocity
  -> full-duration swept-clearance gate before rendering
```

## Scenario: Bind Office Human Animation to Physical Root Motion

### 1. Scope / Trigger

Use this contract whenever an Office crowd review keeps pedestrians visibly
active for a long video. It changes the route-to-animation-to-physics contract
and therefore requires a fresh safety preflight; it is not a cosmetic video edit.

### 2. Signatures

```text
--office-pedestrian-motion-mode single_pass|background_ping_pong|ping_pong
--office-pedestrian-turnaround-hold-seconds <non-negative seconds>
--official-human-animation-mode phase_conditioned|continuous_walk

SCAN_OFFICE_PEDESTRIAN_MOTION_MODE=<same enum>
SCAN_OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS=<seconds>
SCAN_OFFICIAL_HUMAN_ANIMATION_MODE=<same enum>
```

```python
OfficePedestrianRoute.motion_mode: str
OfficePedestrianRoute.turnaround_hold_s: float
office_pedestrian_state(route, sim_time_s) -> OfficePedestrianState
```

### 3. Contracts

- `single_pass` preserves the original wait/walk/arrive schedule and returns
  zero velocity at the endpoint.
- `background_ping_pong` assigns `single_pass` to the two crossing routes and
  `ping_pong` to background routes. `ping_pong` repeats forward walk, stationary
  turnaround, reverse walk, and stationary turnaround using the recorded route
  speed and hold duration.
- The hidden physical capsule, visible human root, truth record, sensor proxy,
  heading, and animation clip all consume the same state. `walk` requires
  nonzero scheduled root velocity; waiting, turning, and arrived states require
  `idle`.
- The run identity records scenario mode, turnaround hold, animation mode, and
  each route's effective mode. `office_pedestrian_motion_audit.json` records
  the corresponding runtime fidelity measurements.
- Changing any route mode or hold invalidates previous swept-clearance evidence.
  Evaluate the full requested duration against both the robot trace and every
  pedestrian pair. Preserve a failing run and use a new run ID after repair.
- RViz window startup is an instrumentation timeout independent of simulated
  duration. `SCAN_RVIZ_STARTUP_TIMEOUT_SECONDS` must be a positive integer and
  long enough for the first bounded RTX/asset preparation on the execution host.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| Motion mode is unknown | Reject before Isaac startup |
| A repeating mode has a non-positive turnaround hold | Reject before runtime |
| Repeating motion uses `continuous_walk` | Reject the review run |
| Root moves while clip is idle, or root stops while clip is walk | Fail motion-fidelity acceptance |
| Crossing route reverses in `background_ping_pong` | Fail identity/schedule validation |
| Full-duration swept clearance fails | Preserve the result and create a new preflight |
| RViz window is absent before its startup timeout | Classify as instrumentation failure, not navigation failure |

### 5. Good / Base / Bad Cases

- **Good:** crossing people walk once and wait safely; background people visibly
  traverse, pause while turning, and traverse back; animation and root velocity
  agree; full-duration safety remains positive.
- **Base:** `single_pass` is valid for the frozen crowd experiment even though
  people eventually stand at their endpoints.
- **Bad:** loop a walk clip on stationary roots, or ping-pong crossing people
  after checking clearance only for their first pass.

### 6. Tests Required

- Unit-test every wait/walk/turn/reverse/arrive boundary, cycle index, heading,
  signed velocity, and per-route mode assignment.
- Acceptance tests must detect walk-while-stationary and idle-while-moving
  samples and verify the frozen 50%/95%/1%/1% fidelity thresholds.
- Before remote rendering, sample the complete duration and assert conservative
  robot/person clearance, pedestrian pairwise surface clearance, and that
  crossing routes never reverse.
- Runtime evidence must show exact visible-root readback, matching moving/walk
  name sets, zero non-foot collision, no hidden termination, and complete goal
  arrival before composition.

### 7. Wrong vs Correct

#### Wrong

```text
continuous walk animation + stationary endpoint
all eight routes ping-pong after a short clearance check
```

#### Correct

```text
one schedule state -> visible root + collision capsule + sensors + truth + clip
crossings single-pass; backgrounds ping-pong with stationary turn holds
  -> full-duration clearance -> runtime motion audit -> human video review
```

## Scenario: Record a Complete, Combined Office Human-Review Video Without a ROS Bag

### 1. Scope / Trigger

Use this contract only when an Office review preflight must show the complete
route through goal arrival and terminal stop, but the execution host cannot
safely store another full point-cloud ROS bag. This is a supplemental visual
run, not formal acceptance evidence and not a replacement for any frozen
candidate. A requested number of seconds alone is not completion evidence.

### 2. Signatures

```text
SCAN_OFFICE_REVIEW_ENABLED=1
SCAN_VISUAL_REVIEW_ONLY=1
SCAN_RECORD_ROSBAG=0
run_remote_office_crowd_native_rviz.sh RUN_ID DURATION TELEMETRY_PORT COMMAND_PORT
```

The new run directory must contain:

```text
effective_input.txt          # records visual_review_only=1 and record_rosbag=0
rosbag.disabled.txt          # explicit non-formal-evidence marker
closed_loop.mp4
closed_loop_third_person_side.mp4
native_scan_rviz3d_5070ti_sim_time.mp4
office_review_terminal_validation.json
office_pedestrian_motion_audit.json
office_review_third_person_rviz_4k.mp4
office_review_third_person_rviz_4k_validation.json
```

### 3. Contracts

- ROS bag recording remains enabled by default. `SCAN_RECORD_ROSBAG=0` is
  accepted only together with `SCAN_VISUAL_REVIEW_ONLY=1` and Office review.
- The run still executes the live simulator, SCAN planner, voxel capture,
  native RViz replay, synchronized video validation, and machine-readable
  runtime audits. Only durable ROS bag writing is omitted.
- Write `rosbag.disabled.txt` and the two effective-input fields so the missing
  bag cannot be mistaken for accidental evidence loss.
- Before composing the review video, reuse the frozen Office goal and terminal
  runtime thresholds. The final pose must be within `0.25 m` of the declared
  goal, and the last continuous `2.0 s` must satisfy both maximum command
  magnitude `0.05` and planar speed `0.15 m/s`.
- Preserve the full-resolution high external side view and native 5070 Ti RViz
  entity videos. Additionally encode one `3840x1080`, 25 fps, H.264/YUV420p
  review video with two `1920x1080` panels: high external side view and
  simulator-time-synchronized native 5070 Ti RViz.
- The combined video frame count must equal `camera_trace.jsonl`; do not align
  quadrants by wall-clock duration or pad an incomplete route with frozen
  frames.
- Always use a new run ID and new output directory. Never overwrite, relink,
  re-encode, delete, or relabel a frozen candidate or an earlier preflight.
- Describe the result as supplemental visual evidence only. It cannot satisfy
  automated acceptance, repeatability, formal reproduction, or human AC55
  until the named reviewer explicitly records the visual decision.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| `SCAN_RECORD_ROSBAG=0` without visual-only mode | Reject before runtime with exit 64 |
| Visual-only mode without Office review | Reject before runtime with exit 64 |
| Visual-only mode while ROS bag recording is enabled | Reject the ambiguous configuration with exit 64 |
| Output directory or any output file already exists | Fail closed; choose a new run ID |
| `rosbag.disabled.txt` is missing or empty | Fail the run |
| Requested duration ends before goal tolerance or continuous terminal stop | Preserve the run, fail before composition, and rerun under a new ID with evidence-based duration |
| Combined resolution, rate, codec, or frame count differs from the contract | Fail the combined artifact and preserve all entity videos |
| Any synchronized video, live RViz audit, or duration gate fails | Preserve the run unchanged and create a new preflight after repair |
| Visual-only run is cited as AC54 or formal evidence | Reject the claim and use the frozen recorded evidence instead |

### 5. Good / Base / Bad Cases

- **Good:** a new 60-second run reaches the Office goal, remains stopped for
  the frozen two-second window, has two decoded simulator-time-synchronized
  entity videos plus a validated 4K-wide two-view composition, retains live RViz
  plan/actual/current/URDF content and explicit visual-only markers, and
  remains pending human review.
- **Base:** a normal review run records its ROS bag by default and may proceed
  through the existing evidence gates.
- **Bad:** silently omit the ROS bag, reuse a candidate directory, then report
  the longer video as a formal replacement or mark AC55 automatically.

### 6. Tests Required

- Shell syntax and ShellCheck must pass for the shared and Office launchers.
- Entrypoint wiring tests must assert the two environment keys, the disabled
  marker, and the fail-closed dependency between them.
- Run the full local bridge test suite before remote execution.
- After the remote run, assert the effective-input fields and marker content;
  decode both delivered entity videos and verify resolution, frame rate, frame count, and
  requested simulator duration; validate the native RViz live audit.
- Validate `office_review_terminal_validation.json` against the frozen goal,
  command, speed, and stop-window thresholds before encoding the composition.
- Decode the 4K-wide composition and assert `3840x1080`, 25 fps, H.264/YUV420p, and
  exact frame-count equality with the shared camera trace.
- Re-hash the frozen candidate acceptance and ROS-event files before and after
  the new run. Leave AC55 pending until the named reviewer decides.

### 7. Wrong vs Correct

#### Wrong

```text
choose 30 seconds -> robot is still mid-route -> pad/freeze frames -> deliver MP4
```

#### Correct

```text
new run ID + evidence-based 60 seconds + explicit visual-only/no-bag markers
  -> live synchronized external-view plus native-RViz run
  -> frozen goal and continuous-stop checks
  -> 3840x1080 two-panel composition with trace-matched frame count
  -> automated video/audit checks -> supplemental delivery
  -> named human reviewer decides AC55
```

## Scenario: Version and Promote Navigation Review Revisions

### 1. Scope / Trigger

Use this contract whenever a reviewed navigation experiment changes source,
configuration, scenario inputs, validation behavior, packaging, or its frozen
presentation contract. It prevents a sequence of ad hoc preflights from being
mistaken for one stable version and keeps automated evidence separate from the
named human decision.

### 2. Signatures

```text
.pipeline/experiments/<experiment>/CHANGE_CONTROL.md
.pipeline/experiments/<experiment>/revision_ledger.json
python3 .pipeline/experiments/<experiment>/validate_revision_ledger.py \
  --ledger .pipeline/experiments/<experiment>/revision_ledger.json \
  --repository-root REPOSITORY_ROOT
```

```text
revision: office-rMAJOR.MINOR.PATCH[-qualifier]
new run: office_crowd_r<major>_<minor>_<patch>_<purpose>_<stage><NN>
stage: smoke | preflight | dryrun | candidate
```

Required ledger fields include `protocol_version`, `experiment_id`,
`current_working_revision`, `accepted_revision`, `formal_candidate`,
`human_gate`, `runs`, and `next_action`. Each run records its revision, stage,
status, immutable flag, claim boundary, and available evidence hashes.

### 3. Contracts

- A revision, run ID, formal candidate, automated gate, human decision, and
  presentation template are different identities. Never use one field or name
  as a substitute for another.
- One new revision declares exactly one change group. `MAJOR` changes the claim
  or core interface; `MINOR` changes one planned behavior; `PATCH` repairs one
  instrumentation, validation, packaging, or presentation behavior without
  changing navigation inputs.
- Retrying identical revision inputs creates a new immutable run ID but not a
  new revision. Any source, config, scenario, validation, or presentation
  contract change creates a new revision before another execution.
- The first ledger created for accumulated historical work may declare itself
  a normalization baseline. It must not fabricate a one-change history for old
  edits. Earlier runs whose exact source revision cannot be reconstructed are
  marked `legacy_unversioned`, not retroactively assigned to the normalization
  snapshot. The one-change rule applies to every later revision.
- A dirty or detached source state may be labeled only as a working/preflight
  revision and must pin the base commit plus source/evidence hashes. It cannot
  become a formal or accepted version until reviewed source is frozen under a
  clean commit and all required gates are rerun.
- Failed, rejected, and superseded runs are immutable. Do not overwrite their
  directories, remove their ledger rows, reuse their run IDs, or relabel their
  claims after repairing a later revision.
- Freezing a golden presentation template controls layout and rendering only.
  It does not accept navigation behavior, satisfy a formal automated gate, or
  decide AC55.
- Before editing, the ledger states the parent, one change group, allowed
  components, frozen invariants, planned validation, claim boundary, and next
  authorized action. After execution, it records the result and exact evidence
  hashes before another change begins.

### 4. Validation & Error Matrix

| Condition | Required behavior |
|---|---|
| A new edit has no declared parent/change group | Stop before editing and create the revision card |
| One revision mixes independent sensor, camera, planner, and gate changes | Split the work into ordered revisions |
| Same inputs are retried after an infrastructure failure | Keep the revision; allocate a new run ID |
| Source/config/gate behavior changes after a failed run | Create a new revision and a new run ID |
| Run ID or result directory already exists | Fail closed; never overwrite or relink it |
| Ledger evidence is missing or its SHA-256 differs | Fail ledger validation and stop promotion |
| Working tree is dirty/detached but status says formal or accepted | Reject the version claim |
| Automated PASS exists but named human gate is pending | Keep human state pending |
| Golden template is approved but the run is incomplete | Freeze only the presentation contract; do not promote the run |
| Full/formal execution has no fresh authorization | Stop at read-only inspection and local validation |

### 5. Good / Base / Bad Cases

- **Good:** one declared revision changes only the MID-360 input, pins its
  parent and invariants, validates locally, uses fresh immutable run IDs, records
  failed and passing evidence separately, and waits for the declared human gate.
- **Base:** an identical-input rerun receives a new run ID under the same
  revision because only transient infrastructure failed.
- **Bad:** repeatedly edit camera, sensor, pedestrian schedule, and validation
  thresholds under one informal `latest` label, then call the newest video the
  accepted version.

### 6. Tests Required

- Parse the ledger as JSON and validate revision grammar, allowed stages and
  statuses, unique run IDs, nonempty change group/invariants/claim boundary,
  and explicit human ownership.
- Recompute every locally available evidence SHA-256 and compare it with the
  ledger before remote execution or promotion.
- Assert that `accepted_revision` and `formal_candidate` remain null during a
  preflight-only task, and that unauthorized full/formal flags remain false.
- Before formal promotion, require a clean reviewed commit, local/remote source
  hash parity, required full dry runs, formal automated acceptance, complete
  artifact sync, and the named human decision.
- Recheck protected historical candidate hashes before and after every new
  remote run.

### 7. Wrong vs Correct

#### Wrong

```text
edit several subsystems -> run preflight42 -> newest video looks best
  -> rename it golden/latest -> assume AC55 and version completion
```

#### Correct

```text
parent revision + exactly one change group + frozen invariants
  -> local validation -> unique immutable run ID -> evidence hashes
  -> automated status and human status recorded separately
  -> fresh authorization for full/formal work
  -> clean frozen source + complete gates + Dr Sun decision
  -> accepted revision
```
