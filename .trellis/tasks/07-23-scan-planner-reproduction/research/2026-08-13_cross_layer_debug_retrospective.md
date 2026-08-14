## Bug Analysis: SCAN Occupancy Was Corrupted Across the Sensor Boundary

### 1. Root Cause Category

- **Category**: B/D/E - Cross-layer contract, test coverage gap, and implicit
  assumptions.
- **Specific cause**: Isaac included a traversable floor that SCAN interprets
  as occupied endpoints; the first obstacle gate accepted floor hits; and
  network-order floats entered a Foxy/PCL cloud without explicit conversion.

### 2. Why Fixes Failed

1. Filtering the floor removed the first symptom but exposed false obstacle
   evidence.
2. Isaac Lab mesh IDs hit a runtime tensor-shape defect in the installed 5.1
   implementation, so that diagnostic was rejected without changing the shared
   simulator installation.
3. A separate obstacle ray-cast mesh established real non-ground sensing, but
   malformed downstream coordinates still marked the robot origin occupied.
4. A known-value network-to-little-endian test discriminated the byte-order
   hypothesis. The next run produced seven successful plans, a physical detour,
   no origin-occupancy errors, and a stopped goal state.

### 3. Prevention Mechanisms

| Priority | Mechanism | Specific action | Status |
|---|---|---|---|
| P0 | Architecture | Convert network points explicitly at the ROS boundary | DONE |
| P0 | Test coverage | Test downstream little-endian float representation | DONE |
| P0 | Runtime gate | Separate ground, filtered, obstacle, and unexpected hits | DONE |
| P1 | Documentation | Add binary sensor and evidence rules to backend spec | DONE |
| P1 | Acceptance | Require physical detour and no collision | DONE |

### 4. Systematic Expansion

- **Similar issues**: command byte order, quaternion ordering, ROS stamp units,
  camera pixel formats, and future intensity/ring fields need the same checks.
- **Design improvement**: serialization owns wire validation; the Foxy bridge
  owns ROS-native conversion; the evaluator owns claims.
- **Process improvement**: sensor gates need discriminating negative evidence
  before planner integration.

### 5. Knowledge Capture

- [x] Updated the backend quality spec.
- [x] Added byte-order and ground-only rejection tests.
- [x] Preserved failed remote runs as instrumentation or integration evidence.
- [x] Complete frozen acceptance and local/remote evidence sync.
- [x] Complete the final Trellis check.

## 6. Formal V1 Failure and Physical-Loop Fixes

The first frozen run was preserved as `acceptance_v1_frozen` and failed three
behavior checks despite reaching the goal: 119.47 N non-foot collision,
0.610 m minimum detour, and 304 failed plan attempts. Offline alignment showed
that the controller advanced B-spline time by wall clock while the articulated
Lite3 lagged the desired position, causing a corner cut into the physical box.

The accepted correction chain was:

1. freeze trajectory progress when planar tracking error exceeds 0.10 m;
2. match SCAN and controller forward speed to the demonstrated V12 limit of
   0.50 m/s;
3. use a 0.40 m Lite3 double-cylinder planning envelope;
4. conservatively occupy 0.70 m behind physical LiDAR hits to represent
   initially occluded obstacle volume; and
5. retain the 20 Hz safety-triggered replanner while disabling distance-only
   periodic replacement of an otherwise safe trajectory.

Two identical-input dry runs passed before `acceptance_v2_frozen`. V2 passed
all 51 frozen checks with zero collision, zero planner failures, and zero
protocol errors. The original threshold file and V1 evidence were unchanged.

## 7. V3 Sensor-Rig Lessons

The first V3 sensor-rig preflight produced empty environmental scans because
the optical self-occlusion mask used broad collision proxies. Those proxies are
valid for contact but too conservative for optical visibility. The failed run
was preserved, and the final implementation ray-casts self-occlusion against
the moving visual geometry while retaining collision primitives for physics.
A second defect was a normal telemetry teardown race: the client could observe
EOF before its stop event and label shutdown as an error. The final runtime
signals the sink before closing the server and stops live transport before
video encoding or simulator teardown.

The durable rule is now in `.trellis/spec/backend/quality-guidelines.md`:
policy identity, asset identity, runtime USD readback, locomotion A/B,
dual-sensor output, failed preflight preservation, frozen acceptance, and
human review are distinct gates.

## 8. V5 Forest Transport Backlog

The first V5 forest closed loop reached its goal and avoided the tree but was
preserved as failed because it recorded one stale-command protocol error, one
reconnect, fourteen sequence gaps, and one watchdog event. A targeted timing
run showed that the geometry filter itself took about 4 ms, while one rendered
forest point transfer/synchronization took about 275 ms. Foxy continued to
send commands during that interval, so its sender and the shared monotonic
clock were excluded.

The root cause was the command receiver's single-frame processing, not the
250 ms limit. A backlog placed old and fresh frames in the same socket buffer;
the receiver rejected the first stale frame and closed before reaching the
fresh latest frame. A failing loopback regression reproduced this with four
stale intermediate frames followed by a fresh fifth frame. The correction
coalesces only frames already buffered, validates and observes every sequence,
and applies the fresh latest frame atomically. A stale latest frame still fails
closed. The regression and the full 5070 Ti scenario then passed without
relaxing source age or watchdog thresholds.
