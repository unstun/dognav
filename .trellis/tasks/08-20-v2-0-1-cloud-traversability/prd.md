# v2.0.1 Point-Cloud Separation and SCAN Traversability Repair

## Goal

Keep the user-facing system version at `v2.0.1` while correcting two connected
boundaries in simulation:

1. RViz must show a truthful, continuously visible live MID-360 cloud including
   the observed ground surface.
2. SCAN must receive a separate obstacle/occupancy cloud and enough terrain
   height information to exercise bounded geometric traversability instead of
   assuming that every route is flat at world `z=0`.

The work must preserve the already completed live-display and transfer-video
repair as immutable evidence. It must not claim learned Lite3 foothold,
friction, contact-stability, or real-robot traversability.

## Confirmed Background

- The completed sibling task
  `.trellis/tasks/08-20-office-r2-0-1-live-cloud-transfer` already repaired the
  slow-wall-clock RViz expiry defect, added fail-closed `/quad_0/cloud`
  observation, and produced a compressed transfer video. Its result history
  must not be renamed, overwritten, or silently reinterpreted.
- The current Office sensor path constructs one planner cloud and publishes it
  as `/quad_0/cloud`; both SCAN and native RViz consume that same filtered
  representation.
- For Office, `run_isaac_v12_fallback.py` removes every hit whose world height
  is at or below `planner_floor_filter_max_z` before serialization. This is why
  the current live display does not represent the complete observed floor.
- The forest path already contains a geometry-only local-minimum terrain filter
  in `isaac_adapter_core.py`. It estimates a local terrain envelope from XYZ
  points and conservatively retains sparse cells; it does not use simulator
  object labels or scene-truth terrain heights.
- The Office planner configuration fixes all preset waypoint heights to
  `0.85 m` and fixes `grid_map.ground_height` to `0.0 m`.
- The Foxy SCAN port suppresses optimization updates in the vertical direction.
  It can preserve a supplied route-height trend, but it does not independently
  discover a safe Lite3 foothold sequence.
- The controller sends horizontal velocity and yaw to the Lite3 locomotion
  interface. Terrain execution therefore remains the locomotion policy's
  responsibility; SCAN can only provide a geometrically admissible route.
- Upstream states that its released defaults are tuned for Unitree Go2. The
  current Office values do not yet have a durable derivation from the pinned
  Lite3 protected-assembly geometry plus V12 terrain qualification, so they
  remain provisional rather than validated Lite3 parameters.
- Dr Sun decided on 2026-08-20 that the first bounded integration should use
  the official upstream Go2 parameters as a reference baseline. This is an
  intentional borrowed-parameter probe, not Lite3 calibration.
- Dr Sun further decided that only the upstream Go2 collision geometry is
  borrowed initially. The existing Lite3 command ceiling (`0.50 m/s`) and
  Office map/horizon remain frozen; the upstream `0.75 m/s` speed and `10 m`
  map are not copied.

## Requirements

### R1. Preserve the completed v2.0.1 repair history

- Keep the public/system version `v2.0.1` and retain every existing preflight
  identifier, hash, failure, master video, transfer video, and rollback record.
- Register this follow-up as a new append-only build/change group before any
  product-code edit; do not mutate the completed sibling task's claims.
- Keep point-cloud display/compression acceptance independent from terrain
  acceptance so either behavior can be diagnosed and rolled back.

### R2. Separate sensor truth from planner representation

- Derive both outputs from the same MID-360 scan and stamp:
  - a raw visual cloud containing all finite in-range environment hits,
    including ground;
  - a planner cloud containing obstacle-like hits after geometry-only terrain
    separation.
- Preserve `/quad_0/cloud` as the planner input unless design review proves a
  remap is safer. Publish the raw visual representation on
  `/quad_0/cloud_raw` and point the native RViz live-cloud display at that
  topic.
- Never send the raw ground-inclusive cloud directly into the occupancy map,
  because doing so would mark the floor as an obstacle.
- Record per-scan raw, filtered-ground, planner, and conservative-retention
  point counts with shared scan identity and timestamps. The authoritative four counts are raw
  finite/in-range points, filtered ground points, planner points, and sparse or
  otherwise unsupported points conservatively retained in the planner cloud.
- Carry the two clouds in one atomic, versioned telemetry payload with body and
  sensor poses, configuration hash, a dedicated monotonically increasing scan
  ID, one timestamp, and independently length-checked point buffers. Reject
  malformed counts/lengths, non-finite values, duplicate or regressed scan IDs,
  missing cloud fields, and any per-cloud or combined payload-limit violation.
- Keep `SENSOR_FRAME_V1` decodable for legacy configurations. The new profile
  must require the dual-cloud message and fail closed if it receives V1 or if
  either configured cloud topic is missing, empty as a name, or aliases the
  other topic. A structurally present zero-count cloud remains representable;
  Office runtime gates decide whether a zero-count scan is acceptable.

### R3. Restore bounded SCAN geometric traversability

- Replace the Office-only constant world-Z floor cut with a local terrain
  envelope that works on flat ground and bounded slopes/steps using measured
  point geometry rather than simulator labels.
- Keep obstacle points above the local terrain envelope in SCAN occupancy.
- Carry a terrain-height/route-height trend into SCAN's 3D waypoints instead of
  clamping every goal to the initial flat body height.
- Record local ground Z, planned body-center Z, and actual odometry body-center
  Z together, with both planned and actual residuals against
  `local_ground_z + body_height`; fail the probe when the declared tolerance is
  exceeded rather than hiding the mismatch.
- Use the exact upstream collision values in the borrowed profile:
  `double_cylinder_radius=0.25 m`, `double_cylinder_offset=0.18 m`,
  `body_height=0.40 m`, `obstacles_inflation_z_up=0.10 m`, and
  `obstacles_inflation_z_down=0.10 m`. Do not copy the upstream speed or map
  horizon.
- Treat `.trellis/tasks/08-20-v2-0-1-cloud-traversability/research/scan-parameter-audit.md`
  as the parameter inventory and provenance record. The upstream geometry's
  implicit step behavior is a borrowed planner assumption, not a qualified
  Lite3 V12 limit.
- Do not invent upstream slope, drop, terrain-fit, or unknown-terrain values;
  upstream exposes none. Use deterministic probe geometry and report its exact
  dimensions without promoting them into general Lite3 capability limits.
- Add a separately named, immutable `upstream_go2_reference` profile rather
  than overwriting the existing Office profile. Copy only values that can be
  traced to the official upstream parameter file, and record every local value
  that has no upstream counterpart.
- Default insufficient/unknown terrain support to blocked for the first probe;
  this safety choice is local and must not be attributed to upstream SCAN.

### R4. Preserve compatibility and safety boundaries

- Flat Office behavior must remain a regression baseline: obstacle avoidance,
  controller topic, MID-360 rate/pattern/range, and pedestrian behavior remain
  unchanged unless separately approved.
- Do not change or retrain the Lite3 V12 locomotion policy in this task.
- Do not run formal training, a real robot, a full-duration formal candidate,
  or AC55 without separate Dr Sun authorization.
- Approval of the final planning summary authorizes task activation, local
  implementation/checks, Foxy build/tests, and the ordered flat Office short
  regression. A non-flat simulation preflight is a separate run gate and must
  wait for a later explicit Dr Sun approval after the flat evidence is shown.
- A passing result may claim only simulated geometric traversability for the
  tested terrain bounds, not general rough-terrain or real-robot capability.

### R5. Evidence and rollback

- Add unit tests for raw/planner topic separation, shared scan identity and
  timestamps, flat ground, sloped ground, step-like height changes,
  sparse/unknown regions, the borrowed vertical-inflation behavior, every
  required malformed dual-cloud input, and legacy V1 compatibility.
- Run one flat regression and separate bounded slope/step simulation probes
  before any longer Office run.
- Archive input parameters, terrain geometry, point-count traces, routes,
  controller outputs, videos, validation reports, hashes, failures, and exact
  rollback instructions.
- Preserve the raw high-quality video and generate a verified compressed
  transfer copy for every human-review run.
- Prove Decay `0` raw-cloud display, immutable historical ledger/run evidence,
  complete transfer-video decode, matching media properties, encoder/version
  provenance, file sizes/compression ratio, master/transfer SHA-256, and
  recursive remote/local artifact-tree parity.

## Acceptance Criteria

- [ ] AC1: The existing completed v2.0.1 live-display/compression evidence is
  byte-preserved and the new build/change group is append-only.
- [ ] AC2: RViz continuously displays a genuine same-run raw MID-360 cloud with
  visible ground; every displayed scan can be matched to the planner scan by
  source identity and timestamp.
- [ ] AC2a: The dual-cloud protocol rejects every declared malformed case,
  enforces monotonic scan identity across reconnects, respects the combined
  payload limit, and retains tested `SENSOR_FRAME_V1` compatibility.
- [ ] AC3: SCAN consumes only the planner cloud; flat ground is not occupied,
  while known obstacles remain represented.
- [ ] AC4: The terrain envelope and route-height path pass deterministic flat,
  bounded-slope, bounded-step, sparse-region, and borrowed-inflation behavior
  tests without claiming a Lite3 terrain limit.
- [ ] AC4a: The exact upstream Go2 reference profile, source URL/commit,
  borrowed values, local-only values, and claim boundary are machine-readable
  and shown in the report.
- [ ] AC5: The flat Office regression retains the frozen sensor, pedestrian,
  planning, and locomotion interfaces and does not regress existing gates.
- [ ] AC6: A short non-flat simulation probe produces reviewable third-person
  plus native-RViz evidence and reports the exact geometric bounds tested.
- [ ] AC7: The report clearly separates geometric SCAN traversability from
  Lite3 locomotion-policy capability and keeps real-robot/general-terrain
  claims out of scope.
- [ ] AC8: The task has a complete change ledger, failure history, artifact
  hashes, and independently usable rollback instructions.

## Out of Scope

- Learned terrain classification or a new neural traversability network.
- Footstep planning, gait selection, friction estimation, slip prediction, or
  contact-stability optimization.
- Policy training or modification in the sibling `machine-dog` repository.
- Real-robot actuation, formal Office promotion, AC55 approval, or a claim of
  general rough-terrain navigation.
- Lite3-specific slope, step, drop, friction, or stability calibration.
