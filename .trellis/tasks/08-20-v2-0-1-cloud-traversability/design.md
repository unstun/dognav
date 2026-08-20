# v2.0.1 Point-Cloud Separation and SCAN Geometry — Design

## 1. Version and claim boundary

The public/system version remains `v2.0.1`. The completed historical revision
`office-r2.0.1-preflight` and its six run directories remain immutable. This
task appends a separately identifiable build:

- revision/build: `office-v2.0.1-go2-geometry-preflight`
- first run ID: `office_v2_0_1_go2_geometry_preflight01`
- collision profile: `upstream_go2_reference`

The build may claim only that the official upstream Go2 collision geometry was
connected to this Foxy SCAN integration and exercised in bounded simulation.
It is not a Lite3 geometry calibration or a Lite3 terrain-capability result.

The official source is pinned to SCAN-Planner commit
`348e8a590a50a5a6bbab8d8c6dcfd171f009be26`, specifically
`src/planner/plan_manage/launch/advanced_param.xml`; a moving `main` URL is
retained only as a human-readable upstream pointer.

## 2. Frozen and changed boundaries

Frozen:

- Lite3 V12 policy, checkpoint, observation/action contracts, and TCP command
  path;
- velocity ceiling `0.50 m/s`, acceleration/jerk, controller gains, Office map
  size/horizon, MID-360 rate/pattern/range/timing, pedestrians, and prior runs;
- `/quad_0/cloud` as the SCAN occupancy input;
- existing master/transfer video contracts and fail-closed compression checks.

Changed:

- one scan carries both raw and planner point sets across the versioned bridge;
- native RViz shows `/quad_0/cloud_raw`, while SCAN keeps
  `/quad_0/cloud`;
- the new planner profile borrows only the official Go2 collision geometry;
- the non-flat probe supplies a route with ground-height Z values through the
  existing SCAN reference-path interface.

## 3. Point-cloud data flow

```text
one MID-360 scan / one timestamp / one scan identity
  |
  +-- finite in-range raw sensor points -----------------> dual-cloud transport
  |                                                        -> /quad_0/cloud_raw
  |                                                           -> native RViz
  |
  +-- local geometry terrain envelope
       +-- supported terrain points -> terrain statistics
       +-- obstacle/unknown points ----------------------> dual-cloud transport
                                                               -> /quad_0/cloud
                                                                  -> SCAN map
```

The raw cloud is never subscribed to by SCAN. The planner cloud is never
presented as the full sensor truth. Both retain the sensor-frame coordinates,
the same ROS stamp, and an audit-visible scan identity.

## 4. Backward-compatible bridge contract

Keep the existing wire header and `SENSOR_FRAME_V1` decoder unchanged for
legacy runs. Add a new versioned telemetry message type for an atomic dual-cloud
sensor frame. Its payload contains:

- the existing body pose, sensor pose, config hash, and point format;
- a monotonically increasing scan identity;
- raw point count and planner point count;
- filtered-ground and conservative-retention counts for audit parity;
- two length-validated XYZ float32 point buffers.

The encoder/decoder must reject negative or out-of-range logical counts,
count/length mismatch, non-finite points, excessive per-cloud or combined
payload size, impossible count relationships, or one missing required cloud.
The stateless payload decoder validates representation; a dedicated bridge-side
scan tracker rejects duplicate or regressed scan identities across reconnects.
The existing stream sequence remains a transport sequence and is not reused as
the scan identity. The new v2.0.1 launch requires the dual-cloud message and
fails closed; legacy launches may continue accepting `SENSOR_FRAME_V1`.

The Foxy bridge publishes both PointCloud2 messages from one decoded frame
before releasing it. This is one transactional decoded source even though ROS
publishes the two messages sequentially. `/quad_0/cloud_raw` and
`/quad_0/cloud` therefore have the same timestamp and frame ID. A compact
per-scan audit row records scan ID, stamp, raw count, filtered-ground count,
planner count, conservative-retention count, publish outcome, and any dropped
or overwritten frame rather than hiding loss.

## 5. Terrain separation

Reuse and harden `local_minimum_obstacle_hits` rather than adding simulator
labels or a second terrain framework. For the new profile only:

1. build the local XY minimum-height envelope from finite, in-range raw hits;
2. classify locally supported points near the envelope as terrain;
3. keep points sufficiently above the envelope as obstacles;
4. keep sparse or unsupported cells in the planner cloud conservatively;
5. serialize raw and planner clouds from the same input scan.

Existing `0.30 m` cells, `0.22 m` height threshold, one-cell neighborhood, and
two-cell support are local provisional filter values. They are recorded as
local-only, not attributed to upstream and not promoted to Lite3 limits.

## 6. Borrowed upstream collision profile

Create a new planner configuration that copies exactly:

- `grid_map.double_cylinder_radius: 0.25`
- `grid_map.double_cylinder_offset: 0.18`
- `grid_map.body_height: 0.40`
- `grid_map.obstacles_inflation_z_up: 0.10`
- `grid_map.obstacles_inflation_z_down: 0.10`

Retain the current Office values for map resolution/size/update range, maximum
ray length, occupancy behavior, manager velocity/acceleration/jerk, planning
horizon, controller gains, and command limits. The profile includes its
official commit-pinned source URL, source commit, and the label
`borrowed_go2_not_lite3_qualified`.

SCAN's paper-style implicit step behavior is tested geometrically from this
vertical envelope. It must not be reported as a Lite3 V12 step capability.

## 7. Route-height contract

The upstream architecture expects a supplied 3D goal/global route; SCAN does
not infer a full traversability route itself. The first non-flat probe therefore
uses the existing reference-path mode:

- each input `nav_msgs/Path` Z value is ground/terrain height;
- the existing SCAN callback adds the borrowed `body_height=0.40 m`;
- B-spline optimization retains the supplied vertical trend while suppressing
  vertical rebound updates;
- the controller continues emitting only horizontal velocity and yaw.

Add validation that path Z is finite and locally consistent. The audit records
local ground Z, planned body-center Z, and odometry body-center Z, plus both
residuals against `local_ground_z + body_height`. A mismatch fails the probe
rather than being hidden. Automatic global terrain-route generation is outside
this patch.

## 8. Display, continuity, and delivery

The existing RViz persistence fix remains. Change only the live display source
to `/quad_0/cloud_raw`. Extend the audit to distinguish:

- raw-cloud generation/reception/nonempty/continuity/visibility;
- planner-cloud generation/reception/nonempty/continuity;
- same-scan timestamp and identity parity;
- ground-visible raw cloud and ground-excluded planner cloud;
- obstacle retention in the planner cloud.

The high-quality master remains immutable after capture. Reuse the verified
CRF comparison, complete-decode, media-parity, legibility, hash, and transfer
selection pipeline for the new human-review video.

## 9. Validation sequence

1. Pure tests: protocol, point classification, topic separation, parameter
   provenance, and route-Z validation.
2. Static synthetic clouds: flat terrain, inclined plane, low/high step-like
   geometry, obstacle above terrain, and sparse/unknown cells.
3. Flat Office regression: prove frozen sensor/planner/controller contracts.
4. Short non-flat simulation preflight: supplied 3D route, raw/planner RViz
   evidence, and exact terrain dimensions.

The approved final plan permits the flat Office short regression only after all
local and Foxy gates pass. The non-flat preflight has a second, separate Dr Sun
run-approval gate after the flat evidence is reported. No real-robot actuation
is allowed.

## 10. Rollback

All new behavior is selected by the new build/profile. Disabling that profile
returns to the existing v2.0.1 behavior without deleting evidence. Before the
runtime commit exists, the ledger records a pre-edit tree SHA, exact owned-file
set, pre-edit hashes, and a path-scoped rollback that is valid only while those
hashes still match. After validation, runtime changes are consolidated into one
reviewed task-owned commit. A second archive-only commit records the resulting
exact `git revert <runtime-commit-sha>` command; this avoids the impossible
self-reference of storing a commit's own SHA inside itself. Run evidence stays
append-only and is not deleted by rollback.
