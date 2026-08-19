# Office Crowd Human-Review Visualization R2 — Implementation Plan

## Phase A — Preserve and Branch

- [ ] Re-check `git status`, current commit, and the existing dirty paths.
- [ ] Record SHA-256 for every candidate38/39 MP4, acceptance JSON, metrics,
  ROS event file, and run identity before implementation.
- [ ] Re-list local and remote candidate namespaces; reserve no existing name.
- [ ] Create/use a child implementation branch rooted at `c17e9da`; stage only
  paths owned by this child task.

**Gate A:** candidate38/39 hashes match the frozen report and no protected dirty
path is modified, staged, copied, or removed.

## Phase B — Inline Local Implementation

- [ ] Preserve the current Office chase-camera equations as the first-view
  compatibility path and add a pure, unit-tested external side-observer camera
  helper with simulator-time smoothing, explicit lateral/trailing/height
  parameters, motion bounds, and desired-versus-realized pose logging.
- [ ] Add an opt-in Office review-material binding plus runtime stage audit;
  leave the URDF and all physical/sensor contracts unchanged.
- [ ] Extend the Isaac runner with a second H.264 writer and camera trace. Both
  views must be rendered at the same simulation step without a second run.
- [ ] Preserve `closed_loop.mp4` as the unchanged first-view compatibility
  stream and add `closed_loop_third_person.mp4` for the external observer.
- [ ] Add a deterministic 3D Office review renderer that reuses existing
  B-spline/time-alignment helpers and consumes genuine XYZ root/plan/occupancy
  samples.
- [ ] Add dashboard metadata, presentation verification, packaging, run
  identity, effective-input, and hash-manifest coverage.
- [ ] Add synthetic tests for camera transforms, same-step dual-view alignment,
  deterministic smoothing, bounded motion, no implicit side flip, output
  hashing, 3D Z sensitivity, occupancy provenance, and fail-closed
  malformed/mismatched streams.
- [ ] Add an opt-in background-only ping-pong pedestrian root-motion schedule
  over the frozen route endpoints, keep the two causal crossings single-pass,
  use phase-conditioned official animation and smooth idle turns, synchronize
  physical/visual/sensor velocity, and add machine-readable fidelity gates.
- [ ] Render the final user-facing composite with only the high external
  third-person and native RViz panels; retain other raw streams internally.
- [ ] Distinguish intermediate RViz waypoints as small yellow markers and the
  unique terminal goal as a larger red marker.
- [ ] Keep all new behavior opt-in and demonstrate legacy trajectory-review and
  non-Office tests remain unchanged.

**Gate B:** Codex stops after local implementation and targeted tests. It does
not create a formal candidate, update AC55, modify hot memory, commit, push, or
archive.

## Phase C — Codex Local Verification

- [ ] Review the complete inline diff against PRD/design and protected paths.
- [ ] Verify source ownership, default-off compatibility, camera-frame math,
  lack of simulator stepping between renders, and absence of planner/sensor
  truth leakage.
- [ ] Run targeted tests:

  ```text
  PYTHONPATH=integration/lite3_sim_bridge \
    python3 -m unittest \
      integration.lite3_sim_bridge.tests.test_trajectory_review \
      integration.lite3_sim_bridge.tests.test_office_review_presentation
  ```

- [ ] Run the full bridge suite:

  ```text
  PYTHONPATH=integration/lite3_sim_bridge \
    python3 -m unittest discover \
      -s integration/lite3_sim_bridge/tests -p 'test_*.py'
  ```

- [ ] Validate task JSONL, JSON/YAML parsing, shell syntax, and owned file list.

**Gate C:** no remote sync until Codex records a clean local review and all
targeted/full tests pass.

## Phase C2 — Dr Sun-Approved MID-360 Input Revision

- [x] Pin the MIT Livox simulator commit, license, clean tree digest, and exact
  `mid360.csv` hash under `references/upstream/2026-08-19_mid360_simulation/`.
- [x] Add an opt-in ordered pattern loader with fail-closed SHA, row-count,
  ordinal, FOV, unit-vector, 10 Hz, and 20,000-ray-per-scan validation.
- [x] Keep legacy uniform mode unchanged by default; select MID-360 explicitly
  only in the Office launcher with 0.1--40 m geometric range.
- [x] Refresh LiDAR rays and pose at one completed Isaac step and publish the
  body pose, sensor pose, cloud, and transport timestamp from that same step.
- [x] Log pattern window, nominal per-point offsets, raw ray count, source
  identity, and the unsupported reflectivity/weather/noise/motion-distortion
  boundary.
- [x] Run local loader/config regressions and one new short remote preflight;
  do not inherit AC54, create a formal candidate, or touch AC55.

### Phase C2 Evidence Record — 2026-08-19

- The source manifest pins Livox commit
  `1cce1073633a062b92e30243a4c2920e45551bb5` and the 800,000-row
  `mid360.csv` SHA-256
  `aa1fc08b6a4400608dbd6ee832b7ea3a9c3c37197e734f60f58fe5abf762269a`.
  The original upstream Gazebo launch remains not reproduced.
- The full local bridge suite passed: 112 tests. Python compilation, both
  launcher syntax checks, JSON/YAML/JSONL parsing, and `git diff --check` also
  passed.
- `mid360_sensor_runtime_smoke01` is preserved remotely as an expected flat
  floor-filter failure: all raw rays were present, but the planner correctly
  removed the only traversable-floor returns. It was not relabeled as a pass.
- `mid360_sensor_runtime_smoke02` passed with a real box obstacle. The final
  instrumented rerun, `mid360_sensor_runtime_smoke03`, also passed and is
  synchronized locally. Across 91 scans it emitted exactly 20,000 rays per
  frame at 10 Hz, exercised all forty source-pattern windows, observed raw
  returns from about 0.944 m to 39.963 m, and held the measured body-to-sensor
  mount at approximately `(0.182399, 0, 0.108541) m` and `15 deg`.
- `office_crowd_mid360_preflight01` is a new five-second Office plus SCAN
  integration preflight, not a formal candidate. It passed the external bridge,
  presentation, and native voxel-capture checks; emitted 51 consecutive
  MID-360 scans with exactly 20,000 rays each; observed about
  15,446--16,202 planner points per scan and raw/planner return ranges up to
  about 39.883 m; and captured 24 nonempty native SCAN snapshots containing two
  trajectory IDs. Local/remote recursive checksum dry-run reported no
  differences.
- The directly openable preflight videos live under
  `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/results/office_crowd_mid360_preflight01/`.
  The three camera streams are 2560 x 1440, 25 fps, 126 frames, and 5.04 s.
  `native_scan_voxel_review.mp4` is 1920 x 1080, 10 fps, 48 frames, and 4.8 s.
  The combined native-SCAN dashboard is 1920 x 1080 and 7.0 s.
- This preflight does not reach the Office goal, does not contain the requested
  complete native-RViz URDF presentation, does not reuse AC54, and does not
  satisfy AC55. Full dry runs and a fresh formal candidate still require fresh
  Dr Sun authorization.

## Phase D — Remote Visual Preflight

- [ ] Confirm `gpu5070ti` identity, GPU availability, Isaac Sim 5.1 runtime,
  remote paths, and absence of a conflicting active run.
- [ ] Sync only reviewed owned files from the local repository to the dated
  Office execution copy and any separate Foxy bridge copy that consumes them.
- [ ] Compare local, Isaac-copy, and Foxy-copy SHA-256 before execution; rebuild
  only the affected remote package if required.
- [ ] Run one short, uniquely named visual preflight with the new review flags.
- [ ] Copy back logs, effective input, both raw camera MP4s, camera trace, 3D
  dashboard, dashboard metadata, material/stage audit, qualification report,
  and complete SHA manifest.
- [ ] Codex decodes every video, checks frame/rate/time parity, runs the new
  validator, creates contact sheets, and inspects contrast, framing, path
  provenance, and obvious visual defects.
- [ ] Require the native RViz audit to prove live B-spline Path, measured body
  Path, current `world -> TORSO`, and measured joint-state delivery; inspect the
  RobotModel and distinct red/green paths in the synchronized capture.
- [ ] Require the pedestrian motion audit to prove all eight names, continuous
  root translation, no walk-in-place, and no idle sliding.
- [ ] Fail and preserve the preflight if the side camera is repeatedly occluded,
  loses the complete robot/nearby interaction, moves abruptly, or requires an
  undeclared side switch; adjust only review-camera parameters in a new run.
- [ ] Bound native-RViz startup with an explicit timeout long enough for Office
  RTX material/texture preparation; preserve a timeout as instrumentation
  failure and never relabel it as navigation evidence.
- [ ] Present the preflight to Dr Sun and wait for a new decision.

**Gate D:** the preflight is visual evidence only. It is not AC54/AC55 evidence
and does not authorize full dry runs or a formal candidate.

### Phase D Evidence Record — 2026-08-19

- `office_crowd_review_pedestrian_motion_preflight01` is preserved as an
  instrumentation failure: the original RViz window wait expired during first
  RTX/texture preparation. The launcher now uses a separate bounded RViz
  startup timeout; the failed directory was not reused.
- `office_crowd_review_pedestrian_motion_preflight02` is preserved as a safety
  failure: all-route ping-pong returned `crossing_1` into Lite3 at about
  21.05 s, with about 0.10 m registered overlap and about 90 N non-foot
  contact. This result was not relabeled as a presentation defect.
- `office_crowd_review_pedestrian_motion_preflight03` uses the approved safe
  mixed schedule: two crossing routes are single-pass and six background
  routes ping-pong with 0.6 s stationary turns. It completed 65.03 s with no
  termination, zero maximum non-foot contact, 0.1134 m final goal error, and a
  passing two-second terminal-stop window.
- The preflight03 pedestrian audit observed all eight people, recorded
  root-motion fraction `0.514649`, timeline-any-motion fraction `0.987388`,
  walk-in-place fraction `0.0`, and idle-sliding fraction `0.0`. The native
  RViz audit passed B-spline, measured path, current pose, root transform, and
  sampling checks.
- The directly reviewable artifact is
  `office_review_third_person_rviz_4k.mp4`: 65.04 s, 3840 x 1080, 25 fps,
  1626 H.264/YUV420p frames, with trace-matched frame count. It remains a
  supplemental preflight pending Dr Sun's explicit visual decision; AC55 is
  unchanged and no formal candidate is authorized by this record.
- Candidate38/39 acceptance and ROS-event SHA-256 values were rechecked after
  preflight03 and still match the frozen evidence.

### Phase D2 Evidence Record — Normalized Change Control

- [x] Separate revision, run ID, formal candidate, automated gate, human gate,
  and presentation-template identities in an experiment-owned control file.
- [x] Record the current accumulated work as the non-formal normalization
  snapshot `office-r2.0.0-preflight`; do not invent a clean release while the
  source remains detached and dirty.
- [x] Freeze `office-dualview-v1.0.0` as the selected presentation template only;
  do not treat the template choice as AC55 acceptance.
- [x] Record `office_crowd_mid360_dualview_preflight01` as an immutable failed
  run and `office_crowd_mid360_dualview_preflight02` as the current short visual
  preflight pending Dr Sun.
- [x] Add a machine-readable ledger with evidence hashes plus a fail-closed
  validator for version grammar, state boundary, unique run IDs, local evidence
  parity, and unauthorized formal/full-run promotion.
- [ ] Before any later source/config change, create one new revision with one
  declared change group and update the ledger before editing or remote running.

**Gate D2:** the ledger may describe a working revision, but only a clean,
reviewed source state plus the declared full gates and Dr Sun's explicit human
decision can create an accepted version. AC55 remains unchanged.

## Phase E — Full Runs After Fresh Authorization

- [ ] After Dr Sun authorizes the full run, execute two same-input 60 s dry runs
  using the unchanged Office safety/goal/causal thresholds plus the new
  presentation checks.
- [ ] Require each dry run independently to pass existing Office acceptance,
  new presentation validation, zero non-foot collision, zero watchdog/protocol
  error, goal tolerance, terminal stop, and at least one strict sensor-causal
  replan.
- [ ] Freeze the effective presentation input only after both dry runs pass.
- [ ] Re-check namespaces and execute one uninterrupted fresh formal candidate,
  expected to be candidate40 only if that name remains unused.
- [ ] Preserve every failed or superseded run unchanged.
- [ ] Sync all formal artifacts locally and compare recursive local/remote
  hashes; run local acceptance and presentation replay.

**Gate E:** a remotely passing run is not sufficient. Local artifact parity,
local replay, complete video decode, and Codex review are required before human
submission.

## Phase F — Human Review and Closeout

- [ ] Deliver the single two-panel third-person + native-RViz composite as a
  directly openable file; retain raw entities in the evidence directory.
- [ ] Explain the review-only robot palette and 3D data provenance.
- [ ] Ask Dr Sun to inspect robot legibility, preservation of the current view,
  genuine side-observer framing, cross-view consistency, articulated motion,
  pedestrians, replanning, plan/actual 3D relationship,
  collisions/interpenetration, and terminal behavior.
- [ ] If rejected, retain the candidate unchanged and open another fresh
  candidate; do not weaken the gate.
- [ ] Only after Dr Sun explicitly accepts: update AC55, parent REPORT/Trellis
  state, hot memory, run final project checks, review staged paths, commit, and
  use `trellis-finish-work`. Archive only durable new facts.

## Owned Paths

- `integration/lite3_sim_bridge/lite3_sim_bridge/run_isaac_v12_fallback.py`
- `integration/lite3_sim_bridge/lite3_sim_bridge/office_crowd_contract.py`
- `integration/lite3_sim_bridge/lite3_sim_bridge/office_crowd_acceptance.py`
- `integration/lite3_sim_bridge/lite3_sim_bridge/trajectory_review.py` only for
  reusable helpers or backward-compatible interfaces
- new Office review presentation module under
  `integration/lite3_sim_bridge/lite3_sim_bridge/`
- `integration/lite3_sim_bridge/lite3_sim_bridge/mid360_pattern.py`
- matching tests under `integration/lite3_sim_bridge/tests/`
- `integration/scan_planner_foxy_ws/src/traj_utils/src/planning_visualization.cpp`
- `integration/scan_planner_foxy_ws/src/plan_manage/src/scan_replan_fsm.cpp`
- `integration/lite3_sim_bridge/config/foxy_native_scan_review.rviz`
- `integration/lite3_sim_bridge/setup.py` only if a new console entry point is
  required
- `.pipeline/experiments/2026-08-13_scan_foxy_isaac_closed_loop/run_remote_closed_loop.sh`
- `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/run_remote_office_crowd.sh`
- new task-owned experiment configs/validators and new run directories
- `references/upstream/2026-08-19_mid360_simulation/` except ignored upstream
  source content, which remains pinned by the tracked manifest
- `.pipeline/survey/2026-08-19_mid360_simulation_upstream_survey.md`
- this child task directory

## Forbidden Paths and Actions

- Do not edit or delete candidate35/38/39 or any older dry run.
- Do not modify sibling `machine-dog`, robot URDFs/meshes or sensor extrinsics,
  checkpoint, SCAN planning behavior, route endpoints, or frozen thresholds.
  The only sensor change is the user-approved opt-in source-backed MID-360
  pattern/range revision with fresh validation; the only schedule change is the
  approved background ping-pong traversal.
- Do not touch unrelated dirty literature, surveys, older logs/results, or
  `docs/research/`.
- Do not update AC55, declare full completion, archive, commit, or push during
  Gemini implementation.
