# Technical Design: Foxy SCAN to Lite3 Isaac Closed Loop

## 1. System Boundary

The implementation deliberately separates the deployment-compatible planner
from the high-fidelity simulation runtime:

```text
Ubuntu 20.04 / ROS 2 Foxy runtime
  SCAN Foxy port
    <- PointCloud2 + simulator-truth Odometry
    -> bounded body-frame Twist
             |
       versioned TCP v1
             |
Ubuntu 24.04 / Isaac Sim 5.1 on RTX 5070 Ti
  simulated 3D LiDAR + truth pose
  pinned Lite3 environment + pinned policy
  articulated joint commands + PhysX contacts
```

ROS messages exist only on the Foxy side. The wire protocol is independent of
ROS distribution and DDS implementation. Isaac remains in its supported host
environment and is not described as a Foxy application.

## 2. Sources of Truth and Planned Layout

- `machine-dog-nav` owns the Foxy port, transport protocol, Isaac adapter,
  launch/configuration, tests, and all result records.
- The SCAN source snapshot is immutable under
  `references/upstream/2026-08-13_scan-planner-ros2-community/`.
- Foxy-specific source and patches live outside that snapshot under
  `integration/scan_planner_foxy_ws/src/`.
- The protocol definition, Foxy bridge, Isaac adapter, and their shared test
  vectors live under `integration/lite3_sim_bridge/`.
- Dated runs and copied-back evidence live under
  `.pipeline/experiments/2026-08-13_scan_foxy_isaac_closed_loop/` or a later
  run-date sibling without overwriting prior evidence.
- `machine-dog` supplies only an immutable, recorded locomotion source revision
  and checkpoint. The current sibling worktree is neither edited nor treated as
  a reproducible dependency.
- Every 5070 Ti directory is a disposable execution copy created from a local
  manifest. A remote-only edit or result is invalid until synchronized back and
  hash-checked.

The exact directory names may gain a later run-date suffix, but these ownership
boundaries must not change during implementation.

## 3. Runtime Environments

### 3.1 Foxy planner side

Use an isolated Ubuntu 20.04 environment on the 5070 Ti and pin the image digest
or equivalent root filesystem identity. A maintained container runtime may be
installed once with Dr Sun's authorization; credentials are entered only into
an interactive privilege prompt and are never echoed, scripted, or persisted.

The selected runtime must support a clean `colcon` workspace, ROS 2 Foxy,
compiler/CMake, PCL, Eigen, and the message/runtime dependencies found in the
pinned package inventory. Foxy is not installed natively on Ubuntu 24.04.

### 3.2 Isaac side

Use the existing Isaac Sim 5.1 / Isaac Lab environment, but launch from a clean
task-owned adapter and a pinned locomotion payload. Before the closed loop, the
run manifest freezes:

- Isaac Sim and Isaac Lab versions;
- source commit and environment configuration;
- checkpoint path and SHA-256;
- robot asset and scene hashes;
- policy observation/action contract;
- command limits and control/physics rates;
- random seed and initial state.

## 4. SCAN Foxy Port

First derive the minimal package dependency graph from the pinned branch. Port
only the path search, B-spline optimization, environment/map, replanning FSM,
trajectory/controller, messages, and launch/config layers needed by the test.

The port must:

- preserve algorithms and numeric defaults unless a Foxy compatibility patch
  is justified and recorded;
- replace Humble-only APIs with the smallest Foxy-compatible equivalent;
- use C++17 only where Foxy toolchain support is verified;
- remove or disable Gazebo Fortress and `ros_gz` dependencies;
- never launch `go2_kinematic_sim` in the acceptance path;
- expose all topic names, frame IDs, rates, map parameters, limits, and goal
  tolerance in one reviewed configuration;
- retain upstream copyright and license notices and record incomplete package
  metadata instead of silently normalizing it.

This result is a project Foxy port. Even if it builds and runs, it is not an
upstream reproduction because the selected upstream branch targets Humble.

## 5. Transport Protocol v1

### 5.1 Topology

Use two TCP streams so high-volume point data cannot head-of-line block the
latest velocity command:

1. **Telemetry:** Isaac -> Foxy, carrying synchronized sensor frames and
   status.
2. **Command:** Foxy -> Isaac, carrying the latest bounded velocity command
   and heartbeat/status acknowledgements as needed.

Endpoints bind only to the local 5070 Ti host/container boundary. They are not
exposed to the public network. Container port publication, if required, binds
to localhost explicitly.

### 5.2 Common frame

Every message uses a fixed-endian length-prefixed envelope containing:

- magic constant and protocol version;
- message type and flags;
- header and payload byte lengths;
- monotonically increasing sequence number;
- simulator or monotonic timestamp in nanoseconds;
- payload CRC32;
- reserved bytes that must be zero in v1.

Receivers enforce maximum header and payload sizes before allocation, tolerate
partial TCP reads, reject unknown required flags, validate CRC and finite
numeric values, and resynchronize only by reconnecting after framing loss.

### 5.3 Telemetry payloads

`SENSOR_FRAME_V1` is one synchronized snapshot containing:

- world-to-base position and unit quaternion;
- world-to-sensor position and unit quaternion;
- point count and packed `float32 x,y,z` points in the declared sensor frame;
- sensor acquisition timestamp and scene/transform configuration hash.

The Foxy bridge converts the snapshot to `sensor_msgs/PointCloud2` and the body
and sensor odometry messages expected by SCAN, using one ROS timestamp. A
separate `STATUS_V1` reports physics/policy/sensor rates, contact state,
termination reason, dropped-frame count, and adapter health.

Point clouds may be voxel-downsampled and capped at an explicitly recorded
limit before transmission. They may not be replaced by static obstacle-map
points.

### 5.4 Command payload

`CMD_VEL_V1` contains `[vx, vy, wz]` as finite SI values in the base frame,
plus sequence and source timestamp. The Foxy side saturates to the intersection
of SCAN and policy limits; the Isaac side independently validates and clamps
again before writing the live command tensor.

Command handling is latest-wins. A configurable watchdog starts with a 250 ms
candidate value and is frozen from measured loop timing before the acceptance
run. Expiry, disconnect, invalid input, simulation pause/reset, or policy error
forces a zero command and records the reason.

### 5.5 Coordinates

The bridge boundary follows REP-103 SI conventions: `x` forward, `y` left,
`z` up; metres, seconds, radians, and right-handed unit quaternions. The Isaac
adapter performs and tests any USD/world conversion once. Frame IDs and the
nominal LiDAR extrinsic are configuration data included in the run hash.

## 6. Locomotion Qualification Gate

Checkpoint selection is evidence-driven and occurs before planner connection.
The first candidate may come from the existing committed Lite3 Isaac evidence,
but it is accepted only if the following one-environment, fixed-seed preflight
passes without training:

1. Apply a safe step schedule containing zero, forward, lateral, yaw, and zero.
2. Record the adapter input, live policy command tensor, command portion of the
   policy observation, action/joint targets, measured base velocity, contacts,
   and termination flags.
3. Confirm command changes occur before inference and produce directionally
   consistent physical response with stable support.
4. Drop the command stream and confirm watchdog zero-command behavior.

If a candidate fails, one already-existing immutable velocity-policy candidate
may be evaluated with the same gate. New training, checkpoint repair, or
silent warm-start is outside scope; failure of all existing candidates is a
documented stop condition.

## 7. Perception and Pose Gate

Use a simulated 3D LiDAR attached to a named Lite3 body frame. RTX LiDAR is
preferred when it can run reliably in the pinned Isaac environment; an Isaac
ray-cast LiDAR is an acceptable minimum because it still renders scene geometry
with pose-dependent occlusion. The final report must state which backend ran.

The first closed loop uses simulator-truth base and sensor poses. It must be
labeled truth odometry, not LIO. The preflight verifies finite/nonempty points,
advancing timestamps, known ground/obstacle returns, transform consistency,
occlusion changes, and motion-dependent observations. No claim is made about
MID-360 beam pattern, intensity, noise, timing, blind zone, or weather response.

## 8. Closed-Loop Scenario and Gate

Use one deterministic course with a flat traversable floor, at least one
collision obstacle requiring planning, sufficient clearance for the Lite3
collision model, a fixed start, and a reachable goal. Freeze the world, seed,
planner configuration, command limits, sensor settings, watchdog, and success /
collision thresholds before the acceptance run.

The causal chain must be observable end to end:

```text
goal -> SCAN trajectory -> bounded cmd_vel -> TCP -> policy command tensor
     -> policy action -> articulated joints -> PhysX motion and contacts
     -> rendered point cloud + truth pose -> TCP -> Foxy topics -> SCAN
```

The success gate rejects base teleportation, direct kinematic integration,
static-map-as-sensor substitution, manual command injection during the run,
NaNs, collision, or an unrecorded reset. Visual evidence must show the actual
run and be paired with machine-readable telemetry.

## 9. Observability and Evidence

Record at minimum:

- exact source/environment/checkpoint/asset/config hashes;
- raw build, test, launch, and runtime stdout/stderr;
- planner trajectory and bounded command stream;
- policy command tensor, measured velocity, actions/joint motion, contacts,
  collisions, resets, and termination reason;
- point count, finite ratio, timestamps, sequence gaps, sensor rate;
- planner/policy/physics rates, bridge latency, reconnects, watchdog events;
- start/goal poses, progress, final distance, and goal result;
- a ROS-side recording and a directly viewable MP4 of the real runtime.

Artifacts are copied back to the local dated experiment directory, hash-checked
against the remote copies, and summarized with the strongest justified evidence
label.

## 10. Rollback and Failure Containment

- All remote files live under one new task-owned directory; existing Isaac and
  sibling workspaces remain unchanged.
- Upstream snapshots are immutable; Foxy changes are isolated in the port or
  reproducible patch files.
- A privileged runtime installation is recorded before/after. Uninstallation
  is a separate destructive action and requires explicit approval.
- The TCP endpoints are local-only, payload-bounded, and fail closed.
- Failure at environment, locomotion, perception, or timing gates stops later
  stages and preserves evidence. It does not trigger training, a ROS distro
  change, a kinematic fallback, or a false success label.

## 11. V2 Validated Baseline Addendum

The accepted implementation retains the architecture above and freezes these
physical-loop decisions for the declared scenario:

- V12 `model_149999` is the pinned locomotion dependency; V17 E3 was rejected
  by the lateral, yaw, and support qualification checks.
- SCAN and the controller use a 0.50 m/s forward limit, with trajectory time
  frozen when planar tracking error exceeds 0.10 m.
- The Lite3 planning proxy is a double cylinder with 0.40 m radius and 0.18 m
  longitudinal offset.
- The occupancy map conservatively adds a 0.70 m occlusion shadow behind each
  physical LiDAR obstacle hit before footprint inflation.
- The 20 Hz safety callback owns collision-triggered replanning; distance-only
  periodic trajectory replacement is disabled for this physical locomotion
  loop.
- Live transport closes at the simulation boundary before video encoding and
  simulator teardown, so shutdown cannot turn queued stale commands into a
  false protocol error.

These values are validated only for the fixed single-box, single-seed
ray-cast-LiDAR Isaac gate. They are not general Lite3 hardware dimensions or a
real-world navigation tuning claim. V2 used the legacy V12 URDF and no D435i
runtime sensor, so it is not the final sensor-rig review target.

## 12. V3 Sensor-Rig Correction

### 12.1 Single-variable locomotion composition

V3 composes the pinned V12 policy/control contract with the pinned V17
Isaac-safe sensor-rig asset. Only the robot spawn asset changes. The V12
checkpoint, policy module, 450-D observation, action order, default pose,
actuator model, control/physics rates, command schedule, seed, and terrain stay
fixed. An old-asset/new-asset A/B qualification precedes any planner run.

The canonical rig URDF and generated Isaac derivative are separate identities:

```text
canonical geometry: d0a1be09f018c0ab31df26f69ad8e700bd88ec06ae5b0f4dfbcc4fddf21cec80
Isaac-safe runtime: 803d552703bcc4f72ce15f38b95bc3f62e3e4ada0b42bf3ecf71b32b6590bb9d
```

The runtime must read back imported links, joints, masses, collision bodies,
sensor-frame prims, and fixed-joint retention. A successful URDF viewer load or
source-level test is insufficient.

### 12.2 MID-360 data path

The navigation point sensor is bound to the imported `mid360_scan_frame`, not a
hard-coded `TORSO` offset. It renders the declared physical course at 10 Hz
using a recorded 360-degree horizontal and `-7..52` degree vertical field of
view. The backend may be RTX LiDAR if a live compatibility probe passes;
otherwise it uses the existing multi-mesh ray caster with an explicit
rig-geometry self-occlusion mask. The latter is named MID-360-like ray-cast
sensing, not a Livox sampling/timing reproduction.

The filtered PointCloud2 path remains the SCAN input. Raw ray count, finite hit
count, floor-filter count, obstacle count, self-occluded count, frame pose, and
timestamp are recorded before transport.

### 12.3 D435i data path

The depth sensor is bound to the imported `d435i_depth_optical_frame` and uses
a scene-rendered pinhole depth backend. V3 records the exact width, height,
focal/aperture representation, FOV, range, update period, clipping behavior,
and optical convention. The local evidence has device-specific RGB intrinsics
but no accepted live depth CameraInfo, so V3 must retain an explicit
provisional-depth-intrinsics label.

D435i depth is not fused into SCAN in V3. It runs concurrently, is checked for
finite/nonempty output, obstacle visibility, pose dependence, and advancing
timestamps, and writes representative depth frames and metrics. Adding depth
fusion would change the planner/perception experiment and requires a separate
reviewed task.

### 12.4 Cross-layer identity

The V3 identity flows through one owner:

```text
asset + mesh hashes + sensor contracts
  -> Isaac scene config and imported prim readback
  -> sensor metrics and TCP frame config hash
  -> Foxy PointCloud2 / odometry
  -> acceptance report, ROS bag, MP4, and local/remote manifests
```

Every consumer records the same asset/sensor configuration hash. A run is an
instrumentation failure if the robot asset hash, sensor frame, expected sensor
output, or depth artifact is absent.

## 13. V4 Native Forest Locomotion Preview

V4 composes the already-qualified V3 Lite3/V12 runtime with the pinned native
`forest_gen` terrain implementation. It does not reuse the upstream Spot task
and does not alter V3 artifacts. `forest_gen` v0.3.8 creates unseeded terrain
and population RNG objects internally, so the adapter explicitly seeds the
terrain strategies and uses a bounded deterministic vegetation layout instead
of claiming that the upstream full population is repeatable. The local
repository owns four separately declared tracks:

```text
forest_gen terrain mesh            -> visual + terrain physics
tree/rock visual USD assets        -> upstream appearance only
source-derived trunk/rock proxies  -> bounded physics + sensor geometry
grass/understory                   -> bounded visual only
```

The first short preview uses one fixed seed and one environment. It places the
Lite3 at a reviewed clear spawn and declares a short zero/forward/yaw/zero
command schedule. A route-relevant obstacle probe precedes locomotion and must
show the same obstacle in visual, PhysX, and both declared sensor geometry
owners. The proxy is labeled source-derived and may not replace the upstream
visual mesh in rendered evidence.

The policy/runtime path is imported from the immutable V3 payload. Before
stepping, V4 asserts the checkpoint, 450-D observation, 12-action order,
default pose, actuator settings, timing, canonical URDF, Isaac-safe URDF, and
sensor frame names. Any mismatch stops the run as an identity failure.

The preview records command, policy action, root pose/velocity, contacts,
support, collision/reset/termination state, sensor obstacle evidence, and raw
viewport frames. Frames are captured during stepping; transport and metrics
are closed before the video writer and simulator teardown complete. Failure is
preserved; no training, controller tuning, SCAN connection, or threshold
relaxation is permitted.

## 14. V5 Faster Forest SCAN Closed Loop

V5 preserves the V3 Foxy/SCAN/TCP/V12 causal chain and the V4 pinned forest,
robot, and sensor identities. It adds a new `forest_gen_nav` course instead of
changing the immutable V4 `forest_gen` preview. The first tree proxy is moved
onto the direct start-to-goal corridor only in this new course. The goal is
fixed at world `(0.5, 3.0, 0.85) m`; the deterministic start is approximately
`(-5.0, 3.0, 0.92) m`, and the primary tree centre is approximately
`(-1.8, 3.0)` with a 0.24 m trunk radius before Lite3 envelope inflation.

The planner data flow is:

```text
raw MID-360-like world hits + sensor pose
  -> finite/range gate
  -> XY cells and neighboring local minimum heights
  -> retain points above the local terrain envelope
  -> existing world-to-sensor conversion and TCP SENSOR_FRAME_V1
  -> Foxy PointCloud2 + truth odometry
  -> SCAN occupancy / safety replan / B-spline
  -> closed-loop controller limited to 0.50 m/s
  -> TCP CMD_VEL_V1
  -> unchanged V12 observation and policy
  -> articulated PhysX motion and fresh sensing
```

The terrain filter is a pure geometry operation. It cannot read the forest
height function, asset type, USD prim path, proxy bounds, or ground/obstacle
labels. Each finite in-range hit is placed in an XY cell. The minimum height
over the cell and its fixed neighboring cells defines the local terrain
envelope; hits above a frozen clearance are planner obstacles. Sparse cells are
retained conservatively. Synthetic sloped-ground, trunk, rock, sparse-return,
non-finite, and range-boundary tests own this contract.

The V3 launch gains optional planner/controller parameter-file arguments while
retaining its current files as defaults. V5 supplies a separate forest planner
configuration and reuses the already-qualified V3 controller configuration.
The common remote runner gains opt-in course and forest-source arguments; its
default remains the V3 single-box course. This avoids a second copied closed-
loop orchestration path.

V5 acceptance does not infer avoidance from video alone. It proves that the
un-inflated direct line intersects the tree envelope, then checks planner
trajectory replacement, command origin, maximum forward command, measured
speed response, lateral detour, minimum root-to-tree clearance, path length,
goal stop, contacts, sensing, transport, ROS bag, and video. V4, every failed
V5 run, and the eventual review candidate remain separate immutable bundles.

### 14.1 Command backlog under simulator sensor stalls

The forest ray-cast workload can occasionally block one simulator Python step
for longer than the 250 ms command source-age limit while physics is not
advancing. The original receiver then violated its latest-wins contract: it
read the oldest queued command, rejected that stale timestamp, disconnected,
and discarded fresher commands already buffered behind it.

The V5 receiver preserves the 250 ms source-age and watchdog limits. It reads
the complete command frames already buffered on the socket as one bounded
batch, validates every frame and monotonically observes every sequence, then
atomically applies only the newest command. Intermediate source-stale commands
are never applied and are counted as intentional coalescing rather than packet
loss. If the newest frame is stale, malformed, non-increasing, or future
skewed, the unchanged fail-closed path rejects the whole batch. Acceptance
records and bounds the number of coalesced frames in addition to requiring zero
sequence gaps, watchdog events, protocol errors, and reconnects.
