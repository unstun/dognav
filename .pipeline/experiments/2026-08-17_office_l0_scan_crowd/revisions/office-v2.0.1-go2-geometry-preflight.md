# office-v2.0.1-go2-geometry-preflight

Status: flat short preflight passed with preserved failures; human review and
separate non-flat authorization pending.

## Why this build exists

The prior single `/quad_0/cloud` was already floor-filtered for planning, so
native RViz could not truthfully show the floor. Feeding a ground-inclusive
cloud to SCAN would instead occupy the floor. This build derives two audited
representations from each genuine MID-360 scan: `/quad_0/cloud_raw` for RViz
and geometry-filtered `/quad_0/cloud` for SCAN.

## Parent and scope

- System version: `v2.0.1`
- Parent: `office-r2.0.1-preflight`
- Profile: `upstream_go2_reference`
- First run ID: `office_v2_0_1_go2_geometry_preflight01`
- Claim boundary: dual-cloud bridge, conservative geometry split, borrowed Go2
  collision envelope, and flat 10.04 s Office preflight only.

The old revision, failed runs, candidate38/39, master/transfer videos, and hash
manifests remain byte-protected by `validate_revision_ledger.py`.

## Borrowed and frozen parameters

Only the following values are borrowed from SCAN-Planner commit
`348e8a590a50a5a6bbab8d8c6dcfd171f009be26`, file
`src/planner/plan_manage/launch/advanced_param.xml`:

- `grid_map.double_cylinder_radius = 0.25`
- `grid_map.double_cylinder_offset = 0.18`
- `grid_map.body_height = 0.40`
- `grid_map.obstacles_inflation_z_up = 0.10`
- `grid_map.obstacles_inflation_z_down = 0.10`

These are Go2 reference values, not Lite3-qualified calibration. The upstream
0.75 m/s velocity was not copied. Lite3 speed remains 0.50 m/s; acceleration,
jerk, Office map/horizon, MID-360 timing/range/pattern, V12 policy/checkpoint,
controller/TCP interface, pedestrians, scene, and acceptance thresholds remain
the current project values.

## Implementation result

- `SENSOR_FRAME_V1` remains unchanged for legacy profiles.
- `SENSOR_FRAME_DUAL_CLOUD_V1` atomically includes poses, configuration hash,
  uint64 scan ID, two clouds, four counts, and one outer timestamp.
- Decode rejects malformed lengths/counts, non-finite points, duplicate or
  regressed IDs, absent required clouds, negative/impossible logical values,
  and payloads over 16 MiB.
- Foxy publishes both PointCloud2 messages consecutively from one decode with
  the same stamp/frame and records a JSONL scan audit.
- Raw points are all finite, in-range returns. Planner points reuse the local
  minimum terrain envelope, remove continuous ground, preserve obstacles, and
  conservatively keep sparse unknowns without using scene labels.
- Native RViz displays `/quad_0/cloud_raw` with Decay 0. SCAN still subscribes
  only to `/quad_0/cloud`.
- SCAN reference-path mode validates finite/continuous path Z, adds 0.40 m body
  height, logs planned/actual/local-ground residual, retains upstream z-gradient
  suppression, and still outputs x/y/yaw control only.

## Direct checks

- Local test command:
  `PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest discover -s integration/lite3_sim_bridge/tests -p 'test_*.py'`.
- Static/archive commands: `python3 -m compileall -q integration/lite3_sim_bridge`,
  `python3 ./.trellis/scripts/task.py validate 08-20-v2-0-1-cloud-traversability`,
  `python3 .pipeline/experiments/2026-08-17_office_l0_scan_crowd/validate_revision_ledger.py --ledger .pipeline/experiments/2026-08-17_office_l0_scan_crowd/revision_ledger.json --repository-root .`,
  three `bash -n` checks for the closed-loop/Office/native-RViz drivers, and
  `git diff --check`.
- Local bridge discovery: 153 tests passed, 2 environment-based skips.
- Ledger validator, Python compilation, shell syntax, Trellis validation, and
  diff whitespace check: passed at archive time.
- Foxy SCAN build: passed. Four CTest targets passed, including six trajectory
  and three reference-height GTests.
- Targeted Foxy bridge suite: 25 passed after preserving the Python 3.8 and ROS
  QoS failures that led to the final source.
- Full Foxy bridge-package collection: not passed because the image lacks
  `torch`, required by an existing MID-360-pattern test.

## Immutable runs

The remote invocation used the task-owned native-RViz wrapper with
`SCAN_CLOUD_PROFILE=upstream_go2_reference`,
`SCAN_REQUIRE_DUAL_CLOUD=true`, the new bridge/planner configuration paths,
Lite3 `SCAN_MAX_VX=0.50`, and the positional arguments
`RUN_ID 10 TELEMETRY_PORT COMMAND_PORT`. Run 01 used ports 46820/46821. Run 02
used 46822/46823 and explicitly set the short-preflight terminal and
full-duration pedestrian gates to zero; the thresholds themselves were not
changed. Each `effective_input.txt` is the canonical expanded input record.

Run 01 failed and remains preserved. It produced 101 scans but only 87 Foxy
audits because the 1 s receive timeout caused reconnects; the wrapper also
applied a full-duration pedestrian gate to the short preview.

Run 02 is the flat 10.04 s successful short preflight: 101 generated scans,
101 Foxy audits, IDs 1--101, and no reconnect or telemetry I/O error. The last
scan records 16,821 raw, 4,842 ground, 11,979 planner, and 14 conservative
points. The stale-module postprocessor failure and missing-NumPy retry remain
present; `live_pointcloud_continuity_audit_retry02.json` passed without a sim
rerun.

The master is 3840 x 1080, 25 fps, 251 frames, 10.04 s, 55,960,853 bytes,
SHA-256 `4e36e06eeb80c3b0d924633af89f61f47b05ca640296b46972c0bc0080618a65`.
The fully decoded H.264 High/YUV420p/BT.709 transfer is 10,664,891 bytes,
SHA-256 `03a9b05b308a323747db782e95c763a6829c9f9b259e989574a88f318339f665`,
an 80.94% reduction (5.25x ratio). The run stores the ffmpeg 6.1.1 identity,
exact command, media probe, and decode result.

## Failure and conclusion boundary

No non-flat simulation, formal training, real robot, complete candidate, AC54,
or AC55 was run. Synthetic inclined/step/sparse fixtures and reference-height
GTests do not demonstrate Lite3 complex-terrain capability, foothold planning,
friction/slip prediction, learned traversability, or gait selection.

Failed builds/tests/runs are never overwritten. New attempts use new IDs. The
remote rosbag and voxel snapshots remain in the isolated execution archive;
the locally recovered human-review/log subset has its own verified recursive
manifest. Run 01's complete remote-tree manifest hash is `f8d1a311...edd68c9`
and its verified 60-file local subset manifest hash is `90abed0e...ca0168a`.
Run 02's complete remote-tree manifest hash is `97dd9c51...7946c3`; its 68-file
human-review/log delivery manifest hash is `6f2da1d7...f17d9c4`.

The exact one-command runtime rollback is:
`git revert 2259afe1964db1495206d67f97e134a9bdf6d5b9`.
