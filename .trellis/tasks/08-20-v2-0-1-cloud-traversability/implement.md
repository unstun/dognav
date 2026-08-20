# v2.0.1 Point-Cloud Separation and SCAN Geometry — Implementation Plan

## Phase A — Register the append-only build

- [x] Recheck current branch/HEAD, dirty paths, task hierarchy, protected run
  directories, and prior `office-r2.0.1-preflight` hashes.
- [x] Append `office-v2.0.1-go2-geometry-preflight` to the revision ledger
  before product-code edits, including parent, allowed paths, frozen values,
  commit-pinned source URL, borrowed/local parameter split, planned run ID,
  gates, artifacts, unauthorized actions, claim boundary, pre-edit tree/path
  hashes, and the exact pre-commit rollback procedure.
- [x] Capture canonical hashes for the historical revision prefix, run records,
  protected master/transfer videos, and existing evidence trees before changing
  the ledger; extend ledger validation/tests without rewriting historical
  entries.

**Gate A:** old evidence is byte-preserved and the new build is registered
before runtime changes.

## Phase B — Add atomic raw/planner cloud transport

- [x] Add tests for a dual-cloud telemetry payload, dedicated scan identity,
  four audit counts, two point counts/buffers, CRC/per-cloud/combined-size and
  finite validation, missing fields, impossible count relationships, duplicate
  or regressed scan IDs across reconnects, and legacy V1 compatibility.
- [x] Implement the new telemetry message type in `protocol.py` and the Isaac
  telemetry sender.
- [x] Compute raw finite in-range points once; derive planner points from that
  scan using `local_minimum_obstacle_hits` for the new profile.
- [x] Extend `foxy_bridge_node.py` to publish `/quad_0/cloud_raw` and
  `/quad_0/cloud` atomically with the same stamp/frame and to record pairing
  evidence.
- [x] Add fail-closed configuration: the new profile requires both clouds;
  requires distinct nonempty topic names; rejects V1; and preserves structurally
  present zero-count buffers. Legacy profiles retain V1 support.

**Gate B:** tests prove that raw points cannot enter SCAN accidentally, planner
filtering cannot alter the raw display, and both topics share scan provenance.

## Phase C — Add the upstream Go2 collision profile

- [x] Add `upstream_go2_reference` as a separate configuration; do not edit the
  historical Office profile in place.
- [x] Copy only radius `0.25`, offset `0.18`, body height `0.40`, vertical-up
  inflation `0.10`, and vertical-down inflation `0.10` from the official file.
- [x] Freeze Lite3 speed `0.50 m/s`, Office map/horizon, sensor, controller,
  policy, pedestrians, and acceptance thresholds.
- [x] Add a machine-readable parameter provenance artifact and tests that fail
  if a borrowed or frozen value drifts. Pin the official source to
  `348e8a590a50a5a6bbab8d8c6dcfd171f009be26`.

**Gate C:** one diff/test report shows exactly five borrowed values and proves
the upstream `0.75 m/s` speed and map/horizon were not copied.

## Phase D — Connect bounded non-flat route height

- [x] Add deterministic flat, slope, step-like, obstacle, and sparse-point
  fixtures for the geometry filter and collision envelope.
- [x] Use SCAN reference-path mode for the non-flat probe, with path Z defined
  as terrain height and SCAN adding `body_height=0.40 m`.
- [x] Add finite/continuity checks and a route-Z/odometry-Z residual audit.
- [x] Verify z-gradient suppression preserves the supplied vertical trend and
  horizontal obstacle avoidance remains active.
- [x] Keep unsupported terrain blocked and label this as a local conservative
  rule, not upstream behavior.

**Gate D:** static and integration tests demonstrate the intended geometry
without claiming a Lite3 slope or step limit.

## Phase E — Update RViz, audits, and delivery

- [x] Point `Live LiDAR Cloud` at `/quad_0/cloud_raw` while preserving decay
  zero, styling, layout, and other panels.
- [x] Extend continuity/audit code and tests for raw continuity/visibility,
  planner continuity, same-scan parity, ground presence/exclusion, and obstacle
  retention, plus explicit raw/ground/planner/conservative-retention counts and
  visible dropped/overwritten scan IDs.
- [x] Keep the master video immutable and reuse the verified compression
  comparison/selection pipeline for the transfer copy.
- [x] Update launch, QoS, rosbag, voxel review, and result manifests to record
  both topics explicitly.

**Gate E:** the displayed cloud is truthful and persistent, while SCAN sees
only the planner representation.

## Phase F — Local quality gate

- [x] First run unit tests and static synthetic point clouds: protocol, adapter,
  flat/inclined/step/sparse geometry, RViz, delivery, parameter, SCAN route-Z,
  historical immutability, and ledger tests.
- [x] Then run the complete bridge tests, including two same-frame PointCloud2
  publications and proof that SCAN subscribes only to `/quad_0/cloud`.
- [x] Run the full `integration/lite3_sim_bridge/tests` suite.
- [x] Only after both Python gates pass, build/test the affected Foxy SCAN
  packages in the declared environment.
- [x] Run Python compilation, JSON/JSONL validation, shell syntax,
  `git diff --check`, Trellis validation, and revision-ledger validation.
- [x] Review all dirty paths and stage only task-owned files.

**Gate F:** no remote execution starts while any local check or provenance gate
fails.

## Phase G — Ordered simulation probes

- [x] Live-check the configured 5070 Ti execution environment, image, display,
  free ports, source hashes, and unused run IDs.
- [x] Use `office_v2_0_1_go2_geometry_preflight01` for the first flat Office
  short regression attempt. Never reuse that ID after either success or
  failure; every retry receives the next unused immutable ID.
- [x] Preserve every flat failure. Report the first passing flat evidence to Dr
  Sun before requesting the separate non-flat run approval.
- [ ] Run one short non-flat reference-path preflight only after the flat gate
  passes and Dr Sun explicitly approves that run. Assign the next unused ID and
  record exact slope/step geometry without calling it a Lite3 limit.
- [ ] Recover the complete artifact tree locally and prove recursive remote /
  local SHA-256 equality.
- [x] Produce directly openable master and compressed transfer videos for Dr
  Sun's review for every successful run that is submitted for human viewing.
  Record encoder command/version, media properties, complete decode, size and
  ratio, both SHA-256 values, and recursive remote/local hash parity.

**Gate G:** automated PASS remains a preflight pending Dr Sun; AC54/AC55,
accepted revision, and formal candidate stay unchanged.

## Phase H — Archive and rollback evidence

- [x] Update revision Markdown/manifest, CHANGE_CONTROL, REPORT, experiment
  README/index, Trellis state, and project `bigmemory/` hot/cold records with
  successes and failures. Do not edit global `/Users/sun/.codex/memories/MEMORY.md`.
- [x] Record why the borrowed Go2 geometry was used, exactly what changed, all
  tests/runs/hashes, known limitations, and the next Lite3 calibration step.
- [x] Preserve the completed sibling task and all old run trees.
- [x] After full review, consolidate runtime/source changes into one task-owned
  commit without unrelated dirty paths. Then create one archive-only commit
  that records the exact `git revert <runtime-commit-sha>` command, so evidence
  remains while runtime behavior can be reverted in one command.

**Gate H:** every claim is reproducible from canonical local evidence and the
borrowed-parameter boundary is explicit.

## Planned validation commands

```bash
PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest \
  integration.lite3_sim_bridge.tests.test_protocol \
  integration.lite3_sim_bridge.tests.test_isaac_adapter_core \
  integration.lite3_sim_bridge.tests.test_delivery_reliability \
  integration.lite3_sim_bridge.tests.test_office_review_presentation \
  integration.lite3_sim_bridge.tests.test_office_revision_ledger

PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest discover \
  -s integration/lite3_sim_bridge/tests -p 'test_*.py'

python3 ./.trellis/scripts/task.py validate \
  08-20-v2-0-1-cloud-traversability
python3 .pipeline/experiments/2026-08-17_office_l0_scan_crowd/validate_revision_ledger.py
python3 -m compileall -q integration/lite3_sim_bridge
bash -n .pipeline/experiments/2026-08-17_office_l0_scan_crowd/run_remote_office_crowd_native_rviz.sh
git diff --check
```

## Pre-start review

- [x] Dr Sun approves the latest `prd.md`, `design.md`, and `implement.md`.
- [x] No product code is edited and `task.py start` is not run before that
  approval.
- [x] Inline execution remains active; no implementation/check sub-agent is
  dispatched.
