# Codex Round 2 Independent Review

- **Task:** `08-17-office-crowd-review-visual-r2`
- **Stage:** `experiment + analysis`
- **Date:** 2026-08-17
- **Reviewed return:** `antigravity-round2-return.md`
- **Decision:** `REJECTED_INCOMPLETE`

## Bottom Line

The second-round implementation is materially more complete than Round 1: the
new module contains a real dashboard renderer, bounded camera math, a USD
material-binding path, and an aggregate validator, and the local test suites
pass. It is not ready for remote preflight or candidate generation because the
evidence validator still accepts fabricated or absent provenance, the material
audit does not perform a post-mutation inventory, and the renderer can overwrite
existing outputs. The return's claim that all five Round 1 P1 findings are fully
resolved is therefore not accepted.

AC55 remains human-owned and pending. No candidate was generated or modified by
this review.

## Independent Checks

### Passing checks

```text
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest \
    integration.lite3_sim_bridge.tests.test_trajectory_review \
    integration.lite3_sim_bridge.tests.test_office_review_presentation

Ran 31 tests in 2.415s — OK
```

```text
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest discover \
    -s integration/lite3_sim_bridge/tests -p 'test_*.py'

Ran 110 tests in 2.787s — OK
```

`py_compile` for the changed Python sources and `git diff --check` also pass.

### Direct fail-open reproductions

Codex generated temporary synthetic H.264/YUV420p inputs and called the real
renderer and validator. The following invalid cases were accepted:

```text
omitted_provenance_passed= True
nan_dt_missing_run_identity_passed= True issues= []
fabricated_material_audit_passed= True issues= []
empty_plan_metrics_passed= True trajectory_ids= [] occupancy= 0 z_range= [0.0, 0.0]
overwrite_allowed= True sentinel_survived= False
```

These reproductions show that green unit tests do not establish the required
fail-closed evidence contract.

## Blocking Findings

### P1 — Validator accepts absent or fabricated provenance

`validate_office_review_presentation()` makes `ros_events_path`, `metrics_path`,
and `run_identity_path` optional and verifies their hashes only when callers
supply existing files. It does not require a non-empty SCAN trajectory,
physical-root series, occupancy XYZ series, run identity, or non-zero real Z
provenance. Its Z check tests only the projection formula using two invented Z
values. Empty ROS events and metrics therefore render and validate successfully.

The camera-trace validator also does not validate a common non-empty run
identity, desired poses, finite positive `dt`, finite positive speed limits, or
the recorded displacement fields. A row containing `dt=NaN` passes because the
numeric comparison against NaN is false.

The material validator checks only a positive declared count and a boolean. It
does not verify affected paths are robot visual meshes, opacity is 1, emission
is 0, pre/post inventories are non-empty and equal, or the robot asset hash is
present. A fabricated audit targeting `/World/Office/Floor` therefore passes.

### P1 — Material audit asserts rather than measures post-state

`apply_office_review_material_usd()` traverses every USD Mesh under the robot
without proving it is visible and non-collision. After binding, it constructs
`post_inventory` by copying `pre_inventory`; it does not re-query bodies,
joints, collisions, mass, sensors, or their target identities. The resulting
`physics_inventory_unchanged` field is circular evidence rather than a runtime
comparison. The USD binding path is also not invoked by the test suite and has
not been verified in Isaac Sim.

### P1 — Immutable-output contract is violated

The renderer exposes an `overwrite` option, the CLI exposes `--overwrite`, and
the Isaac runner explicitly calls the renderer with `overwrite=True`. A
temporary sentinel metadata file was overwritten in the direct reproduction.
This violates the task's never-overwrite evidence boundary and is unsafe for
future candidates.

### P1 — Dashboard causal panel can state unsupported PASS claims

The telemetry panel substitutes defaults when metrics are absent and always
prints `Collision ... -> PASS`, `Watchdog Status: 0 Events`, and compliant
four-foot contact text. These labels are not derived from the frozen acceptance
result and can remain green even for absent or failing evidence. Presentation
must display recorded facts or `unknown`, never synthesize a PASS.

### P1 — Runtime packaging and identity wiring remain incomplete

The task-owned Office and shared remote launchers were not changed, so the new
arguments are not added to `effective_input.txt`. `runtime_composition.json`
does not receive the presentation configuration. `run_identity.json` records
only runner/module hashes, not the task launcher/config identities requested by
the approved contract. The qualification report checks for dashboard files
before rendering them, so the top-level dashboard hash entries are normally
absent after a successful render. This leaves the execution and sync gate
incomplete even before any remote preflight.

### P1 — Required integration regressions are missing

The tests cover pure camera math and a synthetic renderer, but do not invoke the
USD material-binding function or the Isaac runner integration. There is no
runner-level proof that the original first-view equations remain unchanged,
that exactly one physics step feeds both renders, that no `env.step()` occurs
between them, or that writer/trace frame alignment survives runtime teardown.

## Candidate Preservation Check

The report-listed candidate38/39 acceptance JSON and ROS event hashes still
match:

```text
candidate38 office_crowd_acceptance.json b6a759cdf54a42c95a84634d338592d27819989c6c99a92430f05d4b57afffad
candidate38 ros_events.jsonl             7b15be33b15ebfb84a2c2b594114bf365c2cdfa33d7236695b57ae24de346546
candidate39 office_crowd_acceptance.json 8b4f235d172ca6b42dc62ef417699ff6427e939f455db792bc0451c0884d9ca2
candidate39 ros_events.jsonl             1b554788f3eaf18cda67c9bccf90418f6b8d9c542044ecff5983fd7a314e2630
```

The four report-listed candidate MP4 files are not present in this checkout, so
they could not be re-hashed in this review. No candidate38/39 file was written,
renamed, moved, or deleted by Codex.

## Required Round 3 Remediation

1. Make ROS events, metrics, run identity, material audit, camera trace, both raw
   videos, and dashboard metadata mandatory validator inputs and hash all of
   them.
2. Reject empty/non-finite plan, root, occupancy, timing, camera, and real-Z
   provenance. Validate one common non-empty run identity on every trace row.
3. Re-query and compare real post-binding physical/collision/joint/sensor
   inventories; restrict material binding to eligible visible visual meshes.
4. Remove every overwrite path and `--overwrite` option. Use exclusive output
   creation and preserve partial/failed artifacts under a fresh run name.
5. Replace synthetic dashboard PASS labels with recorded values and explicit
   `unknown`/FAIL states.
6. Wire the frozen options and source hashes through the task-owned launcher,
   effective input, runtime composition, run identity, qualification report,
   and final output manifest.
7. Add the missing negative regressions and runner-level same-step/default-off
   integration tests. Isaac-only behavior must remain `BLOCKED` until a real
   runtime preflight is authorized and executed.

Stop again for Codex review after the local Round 3 remediation. Do not run
remote Isaac, create candidate40, update AC55, commit, push, or archive.
