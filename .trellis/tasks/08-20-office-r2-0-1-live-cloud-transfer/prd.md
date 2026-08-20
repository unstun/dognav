# Office R2.0.1 Live Cloud and Transfer Reliability

## Goal

Create the instrumentation-only working revision `office-r2.0.1-preflight`
and presentation contract `office-dualview-v1.0.1`. The revision must keep the
real MID-360 simulator contract at 10 Hz while making the latest same-run live
cloud continuously visible in native RViz, fail closed when that live stream is
missing or invalid, and provide a smaller verified transfer copy of the golden
dual-view video without replacing its high-quality master.

The project stage is `experiment + analysis`. The intended outcome is one
approximately 10-second 5070 Ti visual preflight with locally recovered,
hash-matched evidence that is ready for Dr Sun's visual review.

## Confirmed Background

- The canonical branch was `codex/scan-foxy-isaac` at commit
  `a4efd0ea3cb9e13f70d2b279291916229d09cdc6` before task creation.
- The pre-task worktree had 51 unrelated or pre-existing changes. They are
  user-owned and must not be cleaned, overwritten, staged, or committed.
- `office-r2.0.0-preflight` is the parent working revision and
  `office-dualview-v1.0.0` is its frozen presentation contract.
- `office_crowd_mid360_dualview_preflight02` generated 101 nonempty MID-360
  scans over 10.04 simulator seconds at about 10 Hz. The slow run's wall-clock
  scan arrival gap was much longer: median about 1.89 s, p95 about 2.69 s, and
  maximum about 3.18 s.
- Native RViz directly consumes `/quad_0/cloud` using best-effort sensor QoS.
  Its `Live LiDAR Cloud` display currently uses a 0.4-second decay, so the
  displayed cloud expires long before the next wall-clock arrival.
- The live launch currently sets `require_live_lidar` to false. The replay node
  does not subscribe to `/quad_0/cloud`, and the prior live audit passed with
  `live_lidar_publish_count=0`. This is an audit blind spot, not evidence of a
  faulty sensor rate.
- Candidate38 and candidate39 retain AC54 PASS only for their immutable
  historical inputs. AC55 remains pending and human-owned by Dr Sun.

## Requirements

### R1. Version and change control

- Create revision `office-r2.0.1-preflight` with parent
  `office-r2.0.0-preflight`, presentation contract
  `office-dualview-v1.0.1`, and exactly one change group:
  `golden_dualview_delivery_reliability`.
- Before editing runtime source or configuration, extend
  `revision_ledger.json` to retain append-only revision history and register
  the new planned revision, frozen invariants, allowed components, planned run
  ID, expected artifacts, gates, unauthorized actions, and rollback entry.
- Preserve the complete `office-r2.0.0-preflight` record and all older runs.
  Update the ledger validator and tests for the append-only schema.

### R2. Persistent truthful live-cloud display

- Keep the MID-360 contract unchanged: 10 Hz simulator time, 20,000 rays per
  scan, pinned ordered pattern, 0.1--40 m range, and same-step timing.
- Configure native RViz so a real cloud received from `/quad_0/cloud` remains
  visible until the next real message arrives. Prefer PointCloud2 decay `0`
  after verifying its meaning in the deployed RViz version.
- Do not republish, replay, synthesize, duplicate, interpolate, or post-render
  LiDAR data. Display persistence must not alter the source topic.

### R3. Fail-closed same-run point-cloud continuity audit

- Live mode must subscribe to `/quad_0/cloud` only for observation and set
  `require_live_lidar=true`.
- Produce `live_pointcloud_continuity_audit.json` containing generated scan
  count, received and nonempty counts, first/last ROS stamps, stamp regression
  count, simulator-time and wall-time gap min/median/p95/max, generated/received
  coverage, point-count min/median/max, source topic/mode, cloud-visible video
  frame count, post-warm-up visibility ratio, longest blank run, checks,
  status, and claim boundary.
- Pass only when generated rate remains approximately 10 Hz, coverage is at
  least 95%, all received clouds are nonempty, stamp regression count is zero,
  maximum simulator-time gap is at most 0.2 s, post-warm-up visible-frame ratio
  is at least 98%, and the post-warm-up blank run is at most two video frames.
- Wall-time gaps are evidence only and must not be treated as sensor-frequency
  failures. `require_live_lidar=false` or zero received/published live clouds
  must fail.

### R4. Verified transfer video

- Preserve `office_review_third_person_rviz_4k.mp4` unchanged as the master and
  create `office_review_third_person_rviz_4k_transfer.mp4` as the preferred
  transfer entity.
- Compare CRF 22, 24, and 26 using the same slow preset and select the smallest
  candidate that passes objective and visual-legibility gates; do not select
  an aggressive setting without the comparison record.
- Preserve 3840x1080, 25 fps, frame count, duration, dual-panel layout, H.264
  High, YUV420p, and BT.709. Require complete error-sensitive decoding and at
  least 50% byte reduction.
- Record master and transfer paths, hashes, byte counts, reduction, full encode
  command, ffmpeg/encoder versions, media properties, SSIM, VMAF when
  available, selection rationale, and remote/local hash equality in the
  required ffprobe, validation, SHA, and compression-manifest artifacts.
- RViz text, paths, and live cloud must remain legible. Objective measurements
  support but do not replace direct human inspection.

### R5. Testing and execution evidence

- Add behavior-level regression tests for normal 10 Hz simulator stamps,
  slow wall time, empty clouds, stamp regression, simulator gap over 0.2 s,
  disabled live audit, zero live count, expiring 0.4-second display behavior,
  unchanged `/quad_0/cloud` provenance, and excessive blank video frames.
- Pass targeted tests, the full `integration/lite3_sim_bridge/tests` suite,
  Trellis validation, ledger validation, shell syntax, Python compilation,
  JSON parsing, and `git diff --check` before remote execution.
- Use the configured `compute-helper` workflow to verify Python, GPU/driver,
  native 5070 Ti display, Foxy container, RViz configuration, execution path,
  unused ports, and unused run ID.
- Run only one approximately 10-second visual preflight initially, beginning
  with `office_crowd_r2_0_1_live_cloud_transfer_preflight01`. Preserve every
  failure and increment the run suffix for each retry.
- Recover all evidence to the canonical local result directory and prove
  recursive remote/local SHA-256 equality.

### R6. Archive, commit, and delivery

- Add the revision Markdown and manifest, update change control, ledger,
  validator, report, experiment index, Trellis state, project hot/cold memory,
  and one ad-hoc global-memory update note. Do not edit global `MEMORY.md`.
- Record before/after SHA-256 for each changed task-owned file, commands, run
  IDs including failures, evidence, limitations, and the exact rollback.
- Produce one task-owned fix commit, review the staged path list, and push the
  canonical branch. Rollback is `git revert <fix-commit>`; it must never delete
  retained r2.0.1 evidence or rewrite r2.0.0/candidate38/candidate39.
- Deliver the directly openable local transfer MP4 path plus raw test and
  runtime numbers to Dr Sun.

## Acceptance Criteria

- [ ] AC1: The ledger preserves r2.0.0 and registers r2.0.1 before any runtime
  source/config edit; its validator passes the append-only history.
- [ ] AC2: The deployed RViz display persistently retains the latest genuine
  `/quad_0/cloud` message without replay, republishing, synthesis, or topic
  substitution.
- [ ] AC3: The continuity audit passes all R3 thresholds and fails each declared
  negative regression case.
- [ ] AC4: Runtime evidence still proves the generated simulator-time frequency
  is about 10 Hz with nonempty, increasing-stamp ROS arrivals; wall-time gaps
  are reported separately.
- [ ] AC5: After warm-up, at least 98% of reviewed RViz video frames show live
  cloud and no blank sequence exceeds two frames.
- [ ] AC6: The master is unchanged; the transfer video passes complete decode,
  media/layout parity, objective quality reporting, visual legibility review,
  and at least 50% size reduction after CRF 22/24/26 comparison.
- [ ] AC7: All local quality gates pass before remote execution, and all remote
  artifacts are recovered with recursive SHA-256 parity.
- [ ] AC8: Revision archive, project status records, rollback instructions,
  one task-owned commit, and canonical-branch push are complete.
- [ ] AC9: The final report provides the concrete paths, hashes, sizes, rates,
  coverage, visibility metrics, test summaries, run IDs, rollback commit, and
  the directly openable transfer MP4.

## Out of Scope

- SCAN algorithm or parameter changes.
- Any change to MID-360 frequency, rays per scan, pattern, range, or timing.
- Lite3 V12 policy, robot assets, Office route, pedestrian behavior, or
  acceptance thresholds.
- Candidate38/39 or any existing run directory.
- Full-duration dry runs, a formal candidate, training, or real-robot control.
- AC54 reuse/rerun, AC55 decision, `accepted_revision`, or `formal_candidate`
  promotion.

## Claim Boundary

A passing result may claim only that `office-r2.0.1-preflight` repaired live
cloud display continuity under slow wall-clock simulation, added same-run
fail-closed point-cloud auditing, and verified a compressed transfer path for
one new short preflight awaiting Dr Sun's visual review. It is not a new AC54
result, AC55 acceptance, an accepted revision, a formal candidate, or a
completed Office navigation task.
