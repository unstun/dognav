# Office Crowd Human-Review Visualization R2 — Design

## 1. Design Objective

Improve the human-review presentation without changing the physical navigation
claim. One uninterrupted Office L0 run must preserve the existing delivered
chase-camera view, add a synchronized external side-observer view, and yield a
provenance-linked 3D review dashboard. The pinned Lite3 asset, policy, planner,
sensors, pedestrians, route, collision geometry, and automated thresholds
remain separate immutable identities.

## 2. Confirmed Existing Behavior

- `run_isaac_v12_fallback.py` currently creates one video writer and moves one
  chase camera before each captured Office frame
  (`run_isaac_v12_fallback.py:3287`, `:3597`, `:4453`).
- The Office scene adds a strong dome light (`run_isaac_v12_fallback.py:1854`).
- The same Lite3 asset hash appears in the earlier forest review and the Office
  run, so the visibility regression is environmental/presentational rather than
  an asset-identity change.
- `trajectory_review.py` preserves 3D B-spline samples (`:46`, `:55`) but its
  current bounds, mapper, and actual trace discard Z (`:231`, `:260`, `:407`).
- The Office automated evidence and human-only boundary are recorded in
  `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/REPORT.md`.

## 3. Data Flow

```text
one Isaac physics step
  -> read exact robot/root state
  -> render the existing chase-camera view (no physics advance)
  -> render the external side-observer view (no physics advance)
  -> append both frames with the same step and simulator timestamp
  -> record camera_trace.jsonl

ROS B-spline + captured SCAN occupancy + Isaac root metrics
  + the two hashed raw MP4s + camera trace
  -> deterministic 3D review renderer
  -> synchronized review dashboard MP4 + metadata + hashes
```

## 4. Runtime Presentation Changes

### 4.1 Opt-in and compatibility

All new behavior is disabled by default. Existing `--video-path` behavior and
all non-Office modes remain unchanged. The new Office review mode adds an
explicit path/option for an external side-observer stream, camera trace, and
review appearance.

`closed_loop.mp4` preserves the existing candidate38/39 camera composition and
remains the user-facing first view and compatibility stream. A new
`closed_loop_third_person.mp4` contains the external side-observer view at the
same resolution, frame rate, frame stride, frame count, and simulator-step
sequence.

### 4.2 Review-only Lite3 appearance

After the robot USD is instantiated, bind an opaque, non-emissive high-contrast
review material only to visible robot mesh prims under the imported Robot root.
Do not edit the canonical or Isaac-safe URDF. Do not modify collision APIs,
mass, inertia, joint, sensor target, or policy configuration.

The run identity and stage audit record:

- the opt-in mode and colour/roughness values;
- every affected mesh prim path;
- unchanged robot and referenced-mesh hashes;
- unchanged collision and sensor-target inventories;
- the claim that this is a review visualization, not factory material evidence.

After visual alignment, Dr Sun selected one uniform pure-white robot appearance
instead of part-wise recoloring. Torso, carrier, limbs, and joints therefore use
the same opaque, non-emissive white review material. Legibility is obtained from
consistent lighting, shadows, render quality, and camera exposure rather than
assigning different colors to robot parts. A short visual preflight remains the
gate for this presentation; a failed preflight is preserved and the full run
does not start.

### 4.3 Synchronized cameras

- **First view:** retain the current high, root-relative, offset chase-camera
  equations and bounded wall-occlusion fallback. This is the view Dr Sun called
  first-person; it is intentionally not a literal robot-eye/D435i view.
- **Third person:** add a genuinely external camera beside the robot/scene,
  aimed toward the complete robot and nearby interaction context. It follows
  smoothly from one configured lateral side; it is not fixed, robot-mounted,
  or allowed to snap between sides.
- Compute the desired side-observer pose from the physical root position and
  heading using explicit lateral distance, modest trailing bias, and height
  parameters. Smooth eye and target in simulator time with declared rate limits,
  not wall-clock time, so replay and frame-stride changes remain deterministic.
- Record desired and realized eye/target poses, configured side, smoothing state,
  and any fallback reason for every captured frame. A prolonged occlusion or
  required side flip fails the visual preflight; tune and freeze the configuration
  rather than hiding the defect in a formal candidate.
- Render both views sequentially after the same physics step. Rendering may not
  call `env.step`, advance simulation time, mutate robot state, or use a second
  run. Record a shared `frame_index`, `step`, `sim_time_seconds`, root pose, and
  view-specific eye/target/pose in `camera_trace.jsonl`.
- Any camera occlusion or fallback must be visible in the trace; neither stream
  may be silently replaced by frames from another run or an unrecorded pose.

## 5. Three-Dimensional Review Dashboard

Add an Office-specific renderer that reuses the existing B-spline sampler and
simulator-time association rather than rewriting them. Inputs are read-only and
hashed:

- existing-view raw MP4;
- external side-observer raw MP4;
- `camera_trace.jsonl`;
- `ros_events.jsonl` with complete B-splines and captured inflated occupancy;
- Isaac `metrics.jsonl` with physical root positions;
- `run_identity.json`.

The default `1920 x 1080` dashboard uses four labeled panels: synchronized
existing first view, synchronized external third-person view, an equal-scale
local 3D trajectory view, and causal/event context. Separate raw videos remain
available for full-screen switching.

The 3D panel uses a fixed isometric projection with a fixed metric scale and a
robot-centred XY window. It renders:

- the active sampled SCAN B-spline in world XYZ;
- the accumulated physical root path in world XYZ;
- deterministically downsampled captured SCAN inflated-occupancy XYZ;
- world-axis labels, units, simulator time, and active trajectory ID.

Z participates in the projection and is not exaggerated. Tests must prove that
two points with equal XY and different Z map to different display positions and
that changing Z changes the output metadata/projection. Ground-truth pedestrian
routes may remain separately labeled evaluation context but never substitute
for captured occupancy.

The dashboard metadata records layout, projection parameters, XYZ bounds,
input/output SHA-256, frame-to-simulator-time mapping, plan identities,
occupancy sampling rule, encoder, codec, resolution, rate, and frame count.

## 6. Acceptance and Evidence Integration

The existing Office acceptance remains authoritative for safety, goal,
protocol, watchdog, causal replanning, and collision. A new presentation
validator adds only review-artifact checks:

- both raw streams and the dashboard fully decode as H.264/YUV420p;
- both raw streams have identical frame count/rate/resolution and match the
  camera trace step/timestamp sequence;
- each camera trace row shares the physical state used by both renders;
- the dashboard metadata hashes every input and output;
- the 3D projection consumes finite XYZ and has non-zero Z sensitivity;
- material audit paths are confined to robot visual meshes and physical/runtime
  identities remain unchanged;
- contact sheets contain no blank interval, preserve the existing first-view
  composition, and expose the complete robot and nearby pedestrians in the
  external third-person view.

The new presentation checks cannot convert an automated FAIL into PASS and
cannot satisfy the human-owned gate.

### 6.1 Native Foxy RViz completeness

The native 5070 Ti RViz process consumes only same-run ROS topics. A live review
adapter converts each `/planning/bspline` message into a red ROS Path and
accumulates `/quad_0/body_pose` into a green measured Path. The same body pose
broadcasts `world -> TORSO`. Isaac joint names, positions, and velocities cross
the versioned telemetry protocol and are published as
`/quad_0/joint_states`; `robot_state_publisher` combines those measured joints
with the pinned canonical Lite3 URDF. RViz displays that RobotModel and a TORSO
axis at the current position. The adapter performs no planning and the final
simulator-time video selects only frames from the native screen capture.

### 6.2 Pedestrian animation and root-motion coherence

The legacy Office schedule remains the default `single_pass` mode so historical
inputs can still be reproduced. The corrective review explicitly selects
`background_ping_pong` with a `0.6 s` turnaround hold. The two causal
route-crossing pedestrians traverse once and then idle; each of the six
background routes repeats:

1. forward translation with the official walk clip;
2. stationary endpoint hold with idle clip and smooth 180-degree yaw change;
3. reverse translation with reversed physical velocity and walk clip;
4. stationary start-point hold with idle clip and smooth yaw return.

The visual root, kinematic collision capsule, ray-cast sensor representation,
and recorded velocity consume the same pure schedule state. The run identity
records the schedule mode and hold. A machine-readable audit requires all eight
names, root motion for at least half of person-samples, some person moving for
at least 95% of the timeline, at most 1% walk-in-place, and at most 1% idle
sliding. These checks do not assess natural-looking gait; that remains AC55.

An all-route `ping_pong` preflight was rejected and preserved after the first
crossing pedestrian returned into the Lite3 corridor at about 21.05 s. The
registered surface overlap was about 0.10 m and non-foot contact reached about
90 N. The safe mixed schedule is therefore part of the acceptance contract, not
a presentation-only timing preference.

### 6.3 Final two-panel composition

All raw streams remain immutable run evidence. The directly reviewable output
is a 3840 x 1080 H.264 composition: high external side third-person at left and
simulator-time-synchronized native 5070 Ti RViz at right. The former first-view
and overview streams are not included in the submitted composite.

## 7. Run Sequence and Gates

1. Local implementation and tests in a child branch/worktree.
2. Codex reviews the Gemini diff before any remote sync.
3. Sync only owned sources to both relevant 5070 Ti execution copies and verify
   hashes before running.
4. Run one uniquely named short visual preflight; copy back all logs, both raw
   streams, dashboard, metadata, stage audit, and hashes.
5. Codex verifies root-motion fidelity and presents the two-panel preflight to
   Dr Sun.
6. Only after a fresh explicit authorization, run two same-input full dry runs
   and then one fresh formal candidate (expected candidate40 if still unused).
7. Copy all evidence back locally, run existing and new validators, compare
   local/remote hashes, and submit videos to Dr Sun. AC55 remains unchecked
   until Dr Sun explicitly accepts.

### 7.1 Approved MID-360 revision

The Office launcher explicitly selects `livox_mid360`; all other launchers keep
the legacy `uniform` default. A pinned, ignored upstream checkout supplies the
MIT Livox `mid360.csv`, while a tracked manifest fixes commit, license, file
hash, and tree digest. The bridge validates the exact 800,000-row SHA-256 before
Isaac starts, converts each ordered azimuth/zenith pair to an x-forward,
y-left, z-up unit ray, and advances through forty 20,000-ray scan windows before
cycling.

Each 10 Hz acquisition replaces the ray-direction buffer, marks only the LiDAR
outdated through IsaacLab's public reset API, and performs a zero-dt update.
The resulting sensor pose, body pose, cloud, and transport stamp therefore
refer to the same completed physics step. Nominal per-point offsets are retained
in `sensor_metrics.jsonl`; all rays still use the one snapshot pose, so
intra-scan motion distortion is explicitly unsupported. The raw ray-cast cap is
40 m, while SCAN's own sliding occupancy window stays unchanged and separate.

## 8. Risks and Rollback

- **Dual rendering slows wall time:** preserve the failure; do not relax safety,
  watchdog, or causal timing. Optimize render products or stop for review.
- **Existing-view framing changes accidentally:** fail the compatibility check;
  restore the candidate38/39 chase-camera equations before continuing.
- **External side view is frequently blocked or too mobile:** preserve and fail
  the visual preflight; tune only its lateral distance, height, trailing bias,
  selected side, or smoothing bounds before freezing the full-run input.
- **Review material obscures geometry or appears translucent:** fail the
  preflight. Keep opacity `1.0` and avoid emissive/clay substitutions.
- **3D panel becomes decorative:** fail if source hashes, axes, units, Z
  sensitivity, or simulator-time mapping are missing.
- **Candidate name collision:** select a new directory; never reuse or delete an
  existing run.
- **20,000-ray scan exceeds the pinned runtime budget:** preserve the failed
  preflight and report it; do not reduce point count or range while retaining
  the `livox_mid360` label.
- **Pattern or pose timing mismatch:** fail closed before formal execution; do
  not fall back silently to the uniform sensor.
- Rollback is disabling the new opt-in flags. Existing code paths and
  candidate38/39 remain unchanged.

## 9. Operational Constraint

This Codex session is configured for inline execution. Codex implements and
checks directly without dispatching an implementation/check sub-agent; all
acceptance decisions remain with Dr Sun.
