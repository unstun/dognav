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
