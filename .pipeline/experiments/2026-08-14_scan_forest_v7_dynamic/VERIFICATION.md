# V7 Verification Record

## Frozen identity

- Review run: `forest_v7_review_candidate03`
- R2 frozen acceptance SHA-256:
  `b7d76d52d2596cd13b0d60cc992fa9fa3dac771981488b5addde243a3badb4a3`
- Effective-input SHA-256 shared by dry runs 16, 17, and the review candidate:
  `55ebb9eb7730dd36074fbf17131b3f6a4d1b2722d4ec530bde33d1e20c715fcb`
- V12 checkpoint SHA-256:
  `a9d31dce90e6e8c564d955e473d6d3502f893d7ef5a5c1efaf5bb50d6b3d5450`
- Canonical sensor-rig URDF SHA-256:
  `d0a1be09f018c0ab31df26f69ad8e700bd88ec06ae5b0f4dfbcc4fddf21cec80`
- Isaac-safe URDF SHA-256:
  `803d552703bcc4f72ce15f38b95bc3f62e3e4ada0b42bf3ecf71b32b6590bb9d`

## Qualification sequence

Dry runs 16 and 17 each passed 120/120 with identical source/config inputs and
candidate-threshold hashes. Dry run 16 exercised bounded catch-up from a
0.719 m trajectory-start mismatch; dry run 17 exercised normal tracking. R2
thresholds were then frozen before the review run. The frozen review candidate
passed 120/120 without threshold edits. Candidate 02 had already passed the
same gate, but was superseded after a final cross-scenario review found that
the shared runner had no empty defaults for V7-only hold variables. Candidate
03 records the compatibility-only fix with runner SHA-256
`e7fbeed62c20fd85b4593cb16c99e287d9bf8d3d0a1ceaf72ad7e096905f6cde`.

| Run | Gate | Dynamic clearance | Static-tree clearance | Speed P75 | Final goal error |
|---|---:|---:|---:|---:|---:|
| dryrun16 | 120/120 | 0.899 m | 0.838 m | 0.957 m/s | 0.013 m |
| dryrun17 | 120/120 | 0.249 m | 0.783 m | 0.980 m/s | 0.017 m |
| review_candidate03 | 120/120 | 0.739 m | 0.901 m | 0.954 m/s | 0.089 m |

## Local evidence checks

- Every remote-produced file in dry runs 16 and 17 and the review candidate
  matched its local SHA-256. Each run directory contains `remote_sha256.txt`.
- Raw and overlay videos decode as H.264, 1280x720, 618 frames, 36.35 s.
- The ROS bag SQLite integrity check returned `ok` with 4781 messages.
- All JSON and JSONL evidence parsed successfully.
- Local acceptance re-evaluation passed 120/120.
- The local Python bridge suite passed 68/68. The remote Foxy suite passed
  82 tests with zero failures before the R2 final run.

## Preserved failure boundary

Dry runs 01--15 and preflight 12 remain diagnostic evidence. They include an
audit-regex defect, poorly timed crossing, stale occupied inflation, tracking
freeze, unsafe widened tracking, replan/odometry starvation, catch-up limits,
terminal drift, one real dynamic collision caused by a startup-relative
schedule, one Vulkan device-lost preflight, an over-broad replan-deferral
signal caught by Trellis after candidate 01, and a catch-up policy deadband.
Their fixes led to the
disabled-by-default V7 occupancy freshness window, bounded trajectory catch-up,
catch-up-only replan signal, bounded catch-up command floor, stable-arrival
reporting, and command-relative obstacle schedule. Candidate 01 and no failed
run were relabeled or overwritten.

## Claim boundary

This record supports a frozen automated review candidate for one simulated
forest seed with reactive SCAN occupancy replanning and the pinned V12 policy.
It does not establish human acceptance, predictive dynamic planning, hardware
sensor fidelity, LIO behavior, station keeping, or real-robot safety.
