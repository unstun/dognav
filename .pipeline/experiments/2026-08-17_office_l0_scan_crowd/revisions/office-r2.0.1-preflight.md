# Office R2.0.1 Preflight Archive

> Date: 2026-08-20
> Stage: experiment + analysis
> Revision: `office-r2.0.1-preflight`
> Parent: `office-r2.0.0-preflight`
> Presentation contract: `office-dualview-v1.0.1`
> Change group: `golden_dualview_delivery_reliability`
> Branch: `codex/scan-foxy-isaac`
> Pre-edit commit: `a4efd0ea3cb9e13f70d2b279291916229d09cdc6`

## 1. Outcome and claim boundary

The implementation and the sixth 5070 Ti short run pass the declared
live-cloud, delivered-frame, and transfer-video automated gates. The revision
remains a 10.04-second visual-delivery preflight pending Dr Sun's direct review.
It is not a full route, AC54 rerun, AC55 decision, accepted revision, formal
candidate, upstream SCAN reproduction, or real-robot validation.

`accepted_revision` and `formal_candidate` remain null. Candidate38,
candidate39, the r2.0.0 record, and every existing result directory remain
immutable.

## 2. Confirmed root cause

The sensor itself was not running below contract. It generated 101 genuine
MID-360 scans at 10.0000002 Hz simulator time in the successful short run. The
simulator ran at about 0.051 real-time factor, so the same 0.1 s simulator-time
interval became multi-second wall-clock arrival gaps. RViz's previous 0.4 s
PointCloud2 decay expired the last real cloud before the next real message.

The previous live audit also allowed `require_live_lidar=false`, so a short run
could package output without proving that the native review node observed any
live `/quad_0/cloud` messages. Both defects were presentation/evidence defects,
not a reason to alter the physical sensor schedule.

## 3. Why the 10 Hz MID-360 contract was not changed

The 10 Hz rate, 20,000 ordered rays per scan, pinned Livox pattern, 0.1--40 m
range, and same-step body/sensor/cloud stamp are scientific inputs. Changing
them would create a different sensor experiment and invalidate comparison with
the parent revision. The repair instead retains the latest genuine cloud until
the next genuine arrival and separately records simulator-time and wall-clock
gaps. No cloud is duplicated, republished, replayed, synthesized, or
post-rendered.

## 4. Authoritative RViz semantic evidence

The ROS 2 Foxy RViz PointCloud2 implementation describes decay zero as showing
only the latest points. Its expiration loop removes clouds only when the decay
value is positive; new data replaces the latest cloud. The pinned source used
for this decision is:

`https://github.com/ros2/rviz/blob/foxy/rviz_default_plugins/src/rviz_default_plugins/displays/pointcloud/point_cloud_common.cpp`

The runtime config retains the original display name and `/quad_0/cloud` topic
and changes only `Decay Time: 0.4000000059604645` to `Decay Time: 0`.

## 5. Source changes

- `foxy_native_scan_review.rviz`: latest real live cloud persists until the
  next message.
- `rviz_replay_core.py` and `rviz_replay_node.py`: observation-only live cloud
  receipt, point-count, stamp, simulator-gap and wall-gap evidence; live mode
  fails closed on zero observations.
- `native_rviz_review.launch.py`: live LiDAR auditing is mandatory and the
  observer starts before nonessential publishers.
- `delivery_reliability.py`: deterministic delivered-frame visibility audit,
  ffprobe/full-decode/media-parity checks, CRF comparison, SSIM, optional VMAF,
  and smallest-passing selection.
- Office native driver: finalizes continuity/video evidence and preserves
  partial failure artifacts.
- Shared closed-loop runner: an Office-driver-enabled prestart gate pauses
  Isaac until the original same-container RViz subscriber is attached. It is
  off by default for every other caller.
- Ledger/validator/tests/docs: schema-2 append-only revision history, new
  revision/run records, regression coverage, and claim boundaries.

An experimental separate-container observer was tried in preflight04/05,
received zero DDS clouds, and was removed from the final source. Its failure
evidence remains preserved.

## 6. Pre-edit and implementation hashes

| Path | Before SHA-256 | Implementation SHA-256 |
|---|---|---|
| `run_remote_closed_loop.sh` | `3b780c6480564e594a265a2870e62dcbe3722ba9a12e1ab2f0cbbc6091ee9ba8` | `8e4f749946a4a59e99791ea33155d67889f80265d2767f65ce28cfdb13c89984` |
| `revision_ledger.json` | `b9a886e29004f2248ea2e0e8ecbc8f7869ca36c4c99cdb8b9e128712582f0888` | recorded in the adjacent final manifest |
| `run_remote_office_crowd_native_rviz.sh` | `9fb8341a72d949d80496e16ac69343496e960849e7f848cc7e78c90a295dcad5` | `4e58c0b3472cb324c8a919638ac4a9ae51df64b68c412f898b90a93a5fe1c85b` |
| `validate_revision_ledger.py` | `b04e120633c504b2de31a3a3ccf112108cc93292cb964a69a5c21f2c24b723a5` | `bb94e6a019300ba388dde1150fbe1def7443f44f4f60cd60d8465970c4972ba1` |
| `foxy_native_scan_review.rviz` | `e6ec1a554a990855a708d5904d80c7919c46304018e0cf9365f826060243f8bd` | `c536461b7773c67d5638c90788d7e17774464ce4d397d9cada0654e535b505cb` |
| `native_rviz_review.launch.py` | `9be71bb6bc190d02e8c057ed0a2a9ee31eff914103cfdd52857e077baae3ab7a` | `cb77ca1a4c8ba988f25cd74ffe7913df54d4f11ada9c385b68a81aaaec05e2c1` |
| `rviz_replay_core.py` | `2e1cf623b75dd3c47514dde0036d7a6c6be32d87199497cf477ce45f36ca376f` | `bfd9090003b16fa467cbaca4f210f79cd0926bcbd88769799704e8a8b2c4ab1d` |
| `rviz_replay_node.py` | `7ec51ec856973500283a5ca58341a381374be345de16def8eae1a4198d269972` | `fdbeacd8811e9d3116e4573b97c16e183852a8dd3f4644d82d0c696e5f4120e4` |
| `delivery_reliability.py` | new | `5c7405a8afd49ac58f8cd68d66ff4f567b11fd93e91a6f2443da005c12f025c3` |
| `test_delivery_reliability.py` | new | `6b60ad6907836a451b202d5a9211eaa0848d11a692516046c85ce3a8ddd7665f` |

The manifest records the final hashes after all archive-only edits and is the
machine-readable authority when an archive file appears in this table.

## 7. Local validation history

The final gate uses the project PYTHONPATH and runs the targeted reliability,
presentation, replay-core, and ledger tests plus the full bridge suite. It also
runs the ledger validator, Trellis validation, shell syntax and ShellCheck,
Python compile, JSON parsing, media full decode, and `git diff --check`.

One earlier full-suite command omitted `PYTHONPATH` and invoked the ledger
validator without required arguments, producing import/argument errors. That
was an operator command error, not a code failure; it was preserved as a
pitfall and rerun with the declared commands.

## 8. Remote execution environment and command boundary

The project compute-helper configuration reported no active leased node, so no
formal compute-helper run was claimed. The already configured `gpu5070ti` SSH
execution copy was live-checked instead: NVIDIA RTX 5070 Ti, driver 580.126.09,
16 GiB VRAM, display/Xauthority present, Podman available, Foxy image available,
and ffmpeg 6.1.1 with libx264. The host lacks `/opt/ros/foxy`, so the bridge was
built inside the pinned Foxy container rather than on the host.

Each run used the Office native-RViz driver with a unique run ID, 10-second
duration, native display enabled, and the full-route terminal and pedestrian
fraction gates explicitly skipped/not gated. The local checkout remained the
source of truth; only reviewed task-owned sources were synchronized, their
hashes were checked, and the result tree was recovered to the matching local
experiment path.

The successful remote invocation was:

```bash
SCAN_NATIVE_RVIZ_REQUIRE_TERMINAL_GATE=0 \
SCAN_NATIVE_RVIZ_REQUIRE_PEDESTRIAN_MOTION_GATE=0 \
bash run_remote_office_crowd_native_rviz.sh \
  office_crowd_r2_0_1_live_cloud_transfer_preflight06 \
  10 39201 39202
```

The final local validation commands were:

```bash
PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest \
  integration.lite3_sim_bridge.tests.test_delivery_reliability \
  integration.lite3_sim_bridge.tests.test_rviz_replay_core \
  integration.lite3_sim_bridge.tests.test_office_review_presentation \
  integration.lite3_sim_bridge.tests.test_office_revision_ledger
PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest discover \
  -s integration/lite3_sim_bridge/tests -p 'test_*.py'
python3 .pipeline/experiments/2026-08-17_office_l0_scan_crowd/validate_revision_ledger.py \
  --ledger .pipeline/experiments/2026-08-17_office_l0_scan_crowd/revision_ledger.json \
  --repository-root .
python3 .trellis/scripts/task.py validate 08-20-office-r2-0-1-live-cloud-transfer
bash -n .pipeline/experiments/2026-08-13_scan_foxy_isaac_closed_loop/run_remote_closed_loop.sh
bash -n .pipeline/experiments/2026-08-17_office_l0_scan_crowd/run_remote_office_crowd_native_rviz.sh
python3 -m compileall -q integration/lite3_sim_bridge
git diff --check
```

## 9. Immutable run history

| Run | Outcome | Preserved reason |
|---|---|---|
| `office_crowd_r2_0_1_live_cloud_transfer_preflight01` | FAIL | 101 generated / 99 observed, but installed launch still had `require_live_lidar=false`; fail-closed audit rejected it. |
| `office_crowd_r2_0_1_live_cloud_transfer_preflight02` | FAIL | 95/101 = 0.940594 coverage, below 0.95; video visibility itself was 251/251. |
| `office_crowd_r2_0_1_live_cloud_transfer_preflight03` | FAIL | Node reorder alone still yielded 95/101; generic startup race remained. |
| `office_crowd_r2_0_1_live_cloud_transfer_preflight04` | FAIL | Separate prestarted observer reached READY but received zero cross-container DDS clouds. |
| `office_crowd_r2_0_1_live_cloud_transfer_preflight05` | FAIL | Matching the separate container identity still yielded zero; abandoned observer removed. |
| `office_crowd_r2_0_1_live_cloud_transfer_preflight06` | automated PASS, human review pending | Original same-container subscription prestart gate passed; all declared short-run delivery gates passed. |

The full failed remote directories are preserved. Their lightweight audit,
identity, exit and log evidence was also recovered locally; no failed result
was overwritten or renamed.

## 10. Successful continuity and visibility measurements

- Generated: 101 scans at 10.0000002 Hz simulator time.
- ROS received: 96 nonempty clouds; coverage 0.9504950495.
- Stamps: first 29,999,999 ns, last 10,029,999,775 ns, zero regressions.
- Simulator gaps: min 0.100 s, median 0.100 s, p95 0.130 s, max 0.200 s.
- Wall gaps (record only): min 1.434 s, median 1.898 s, p95 3.218 s,
  max 4.899 s.
- Points/cloud: min 15,208, median 15,569, max 16,202.
- Delivered video: 251/251 visible frames after warm-up, fraction 1.0,
  longest blank run 0 frames.

The live audit is
`results/office_crowd_r2_0_1_live_cloud_transfer_preflight06/live_pointcloud_continuity_audit.json`,
SHA-256 `b5c22581555ad46fb4f9ebd3899cd0cc5e597388a815d802980161c36c263c7e`.

## 11. Transfer-video selection

| Entity | Bytes | Reduction | SSIM | Result |
|---|---:|---:|---:|---|
| Master | 58,781,800 | baseline | 1.0 | preserved |
| CRF 22 | 18,640,083 | 68.29% | 0.983774 | PASS |
| CRF 24 | 14,637,497 | 75.10% | 0.979406 | PASS |
| CRF 26 | 11,543,483 | 80.36% | 0.974314 | PASS, selected smallest |

Both master and transfer are 3840x1080, H.264 High, YUV420p, BT.709,
25 fps, 251 frames, and 10.04 s. Both fully decode. VMAF is recorded as
unavailable because the deployed ffmpeg has no libvmaf filter. The master SHA is
`f3da239ddab98816efba855b83d1bbf30d645688eb5987c63f47405c3e9bb27f`;
the transfer SHA is
`d0d8cbb3e2ed1347e91f3ecec732b47a3f4614cbdd0c3d579a5a3b0408f3591d`.

## 12. Evidence recovery and provenance

The canonical result path is
`.pipeline/experiments/2026-08-17_office_l0_scan_crowd/results/office_crowd_r2_0_1_live_cloud_transfer_preflight06`.
The complete 8.6 GiB remote tree, including the 8.2 GiB rosbag database and
voxel snapshots, was transferred as a SHA-256-checked zstd archive, extracted at
that canonical path, and compared with sorted recursive SHA-256 manifests. The
temporary archive SHA-256 was
`50112b8076410ce9ab0c690d2f15ace73e7b9f39280dccfdea984f8609a3c4ab`;
it and its transport splits were removed only after extraction and parity.

The final remote and local trees each contain 128 files. Their manifest files
are byte-identical and each has SHA-256
`a2bffd7c2aa9dc7174c4993e5365d1e27735fc8aaba3ad2372c273b798d333ba`.
They are stored beside this archive as
`office-r2.0.1-preflight.remote-recursive-sha256.txt` and
`office-r2.0.1-preflight.local-recursive-sha256.txt`. Large media and runtime
artifacts remain local-only under the repository's binary policy; their textual
hashes and archive metadata are Git-backed.

## 13. Rollback and next authorized step

After the single fix commit is created, rollback is exactly:

```bash
git revert <office-r2.0.1-fix-commit>
```

Reversion restores the 0.4 s display decay and previous audit/package behavior
but deliberately retains all r2.0.1 evidence and does not rewrite r2.0.0 or
candidate38/39.

Concretely, the revert restores `Decay Time: 0.4000000059604645`, restores the
old live-launch setting in which `require_live_lidar` was false, removes the
observation-only continuity/prestart gates, and stops producing the CRF transfer
entity and its validation package. To inspect the preserved parent after the
revert, run the reverted `validate_revision_ledger.py` against
`revision_ledger.json`; that validator sees the restored schema-1 r2.0.0 current
record. The revert must not delete any `office_crowd_r2_0_1_*` result directory,
candidate38, or candidate39 evidence. The r2.0.1 archive remains recoverable
from the reverted fix commit in Git history even though the working-tree
control plane returns to r2.0.0.

The only next step authorized by this archive is Dr Sun's direct review of the
local transfer MP4. A full-duration dry run, fresh AC54 candidate, AC55 decision,
formal-candidate assignment, training, or real-robot actuation requires a new
explicit authorization.
