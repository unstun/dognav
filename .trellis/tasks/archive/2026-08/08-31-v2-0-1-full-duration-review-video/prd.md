# v2.0.1 60-second Office review video

## Goal

Produce one new immutable 60-second Office L0 dual-view human-review video from
the current `office-v2.0.1-go2-geometry-preflight` flat-scene implementation.
The result must exercise the full-duration endpoint, terminal-stop, pedestrian
motion, dual-cloud, native-RViz, and delivery gates while remaining a dry run
pending Dr Sun's review.

## Background and authorization

- Dr Sun explicitly selected the 60-second complete-duration option on
  2026-08-31 after being offered a 30-second review-only alternative.
- Canonical source is the local `machine-dog-nav` checkout on
  `codex/scan-foxy-isaac`. Remote 5070 Ti workspaces are execution copies.
- Current working revision is `office-v2.0.1-go2-geometry-preflight`; the latest
  passing flat short run is `office_v2_0_1_go2_geometry_preflight02`.
- The new run is flat Office L0 with the existing `upstream_go2_reference`
  profile. It is not the separately gated non-flat probe.
- Existing runs, masters, transfer files, hashes, and failure evidence are
  immutable.

## Requirements

### R1. Register one full-duration dry run before execution

- Append the authorization and planned run
  `office_v2_0_1_go2_geometry_dryrun01` to the Office revision ledger before
  remote execution.
- Keep `accepted_revision` and `formal_candidate` null and AC55 pending.
- Record the exact local source commit/tree, task-owned synchronized paths,
  remote execution root, expected artifacts, gates, and failure boundary.
- If the run ID exists locally or remotely, preserve it and use the next unused
  suffix; never overwrite or repair a run directory in place.

### R2. Preserve current scientific and presentation inputs

- Use the current flat Office L0 scene, eight-pedestrian behavior,
  `upstream_go2_reference` dual-cloud profile, Lite3 V12 policy, 0.50 m/s
  ceiling, MID-360 timing/pattern/range, route, planner parameters, and golden
  dual-view layout without modification.
- Keep raw `/quad_0/cloud_raw` for truthful native-RViz display and planner
  `/quad_0/cloud` for SCAN; require same-scan identity/stamp pairing.
- Do not activate non-flat geometry, change the planner, train a policy, or
  actuate a real robot.

### R3. Run exactly one 60-second full-duration attempt at a time

- Execute `run_remote_office_crowd_native_rviz.sh` with duration `60` and the
  default full gates enabled:
  `SCAN_NATIVE_RVIZ_REQUIRE_TERMINAL_GATE=1` and
  `SCAN_NATIVE_RVIZ_REQUIRE_PEDESTRIAN_MOTION_GATE=1`.
- The run must meet the existing minimum 50-second simulator duration, reach
  the frozen goal within 0.25 m, and show a continuous two-second terminal
  stop within existing command/speed bounds.
- Full-duration pedestrian motion, dual-cloud pairing/continuity, raw-cloud
  visibility, planner separation, runtime safety, and video validation must
  fail closed.
- A failure is preserved and reported. Any retry uses `dryrun02`, `dryrun03`,
  and so on; no threshold is relaxed silently.

### R4. Preserve a master and deliver a sub-10 MB review copy

- Preserve the 3840x1080, 25 fps dual-view master and the existing standard
  transfer output; neither may be overwritten.
- Add `office_review_third_person_rviz_4k_transfer_under10mb.mp4`, strictly
  smaller than 10,000,000 bytes and directly playable.
- The sub-10 MB copy must retain the complete frame sequence, duration, 25 fps,
  two-panel ordering, H.264 High, YUV420p, and BT.709. Resolution may be reduced
  only for this explicitly labeled delivery copy; the 4K master remains the
  visual authority.
- Prefer 1920x540 (960x540 per panel) with a conservative two-pass size target.
  Validate complete decode, frame/duration parity, master hashes unchanged,
  SSIM against a same-resolution master reference, and direct legibility of
  robot, paths, point clouds, and major RViz text. If that quality gate fails,
  do not deliver a worse encode as PASS.

### R5. Recover canonical evidence and report exact boundaries

- Copy the master, sub-10 MB entity, standard transfer entity, driver log,
  audits, ffprobe data, validations, SHA-256 files, and a remote recursive
  manifest into the canonical local result path.
- Compare every recovered file to the remote manifest by SHA-256. Preserve the
  complete raw result tree remotely; do not claim local full-tree parity unless
  all raw rosbag/voxel files are actually copied.
- Update the append-only ledger, report, Trellis record, and project memory with
  the run outcome and exact evidence scope.

## Acceptance Criteria

- [x] AC1: A new immutable 60-second dry-run ID is registered before execution;
  prior runs and artifacts are byte-preserved.
- [x] AC2: Source hashes match between local canonical paths and the 5070 Ti
  execution copy before launch; the chosen ports are free.
- [x] AC3: The run records at least 50 seconds of simulator time, reaches the
  frozen goal within 0.25 m, and passes the two-second terminal-stop gate.
- [x] AC4: Full-duration eight-pedestrian root-motion/animation checks pass.
- [x] AC5: Dual raw/planner clouds remain paired with zero scan-ID/stamp
  regressions, raw display is continuous, and SCAN consumes only planner cloud.
- [x] AC6: The 3840x1080 master and synchronized native-RViz composition fully
  decode with matching trace/frame count and unchanged layout.
- [x] AC7: A separate directly playable transfer entity is `<10,000,000` bytes,
  fully decodes, covers the full duration/frame sequence, preserves panel order,
  passes declared objective quality checks, and leaves every earlier artifact
  unchanged.
- [x] AC8: Recovered canonical-local evidence matches the remote hashes for the
  declared delivery subset, and any non-recovered raw artifacts are explicitly
  listed as remote-only.
- [x] AC9: The outcome remains a full-duration dry run pending Dr Sun review;
  AC55 stays pending and no accepted/formal identity is assigned automatically.

## Out of Scope

- Non-flat simulation, general traversability, or Lite3 terrain-capability
  claims.
- Formal candidate promotion, AC55 approval, or rewriting AC54 history.
- Planner/sensor/policy/robot/route/pedestrian/threshold changes.
- Training, real-robot actuation, or deletion of any prior evidence.

## Blocking open questions

None. Dr Sun selected the 60-second option and the repository fixes the current
v2.0.1 flat Office inputs, full-duration gates, and sub-10 MB delivery rule.

## Outcome

`dryrun01` was preserved as a delivery-pipeline failure. Detached `dryrun02`
passed the declared flat 60-second gates. The preferred 1920x540 compression
attempt failed its quality floor and remains negative evidence; the separate
1280x360 `_under10mb_v2` artifact passed at 9,176,726 bytes and SSIM 0.964990.
The result remains pending Dr Sun's human AC55 decision.
