# Gemini Execution Package — Office Crowd Review Visualization R2

## Active Task

`.trellis/tasks/08-17-office-crowd-review-visual-r2`

Read, in order:

1. `AGENTS.md`
2. the active task `prd.md`
3. the active task `design.md`
4. the active task `implement.md`
5. `.trellis/spec/backend/quality-guidelines.md`, especially the sensor-rig,
   moving-obstacle, and Office L0 crowd scenarios

## Source of Truth

The local `machine-dog-nav` Git repository is the only code and project-state
source of truth. Work in the explicitly provided local child-task checkout.
The 5070 Ti workspace is an execution copy only. A remote-only modification or
success is invalid.

## Current Execution Boundary

Implement **Phase B only**. Stop after local edits and local targeted tests.
Do not use SSH, sync remote files, run Isaac, create a candidate, commit, push,
update AC55, update parent reports/hot memory, or archive.

## Objective

Implement opt-in Office review presentation support that:

- gives the Lite3 a documented review-only high-contrast appearance without
  changing its URDF, physics, sensors, policy, or planner;
- preserves the current candidate view as `closed_loop.mp4` and records a
  synchronized external side-observer H.264 video from the same run;
- records a frame/step/simulator-time camera trace;
- creates a deterministic 3D dashboard from hashed SCAN B-splines, captured
  inflated occupancy, physical root metrics, and the two raw videos;
- preserves all legacy behavior by default.

## Allowed Modification Scope

Only the `Owned Paths` listed in `implement.md`. Add the smallest new module and
tests needed. Search existing helpers before creating new utilities.

## Prohibited Scope

- candidate35/38/39 and all existing results;
- sibling `machine-dog` and all robot URDF/mesh/checkpoint files;
- SCAN planning/controller semantics, safety thresholds, Office route, or
  pedestrian schedules;
- unrelated dirty files;
- claims, acceptance checkboxes, commits, pushes, archives, or remote runs.

## Required Engineering Behavior

- Keep new flags default-off and preserve the current `--video-path` contract.
- Preserve the existing Office chase-camera equations exactly as the first-view
  compatibility stream; do not replace them with a D435i/robot-eye viewpoint.
- Implement the approved smooth side-following external observer: one configured
  lateral side, explicit lateral/trailing/height parameters, simulator-time
  smoothing, bounded motion, and desired-versus-realized pose logging. Do not
  implement a fixed camera, an orbit, implicit side flips, or frame cuts.
- Render both views without a physics step between them and record shared state.
- Keep opacity at `1.0`, use non-emissive review materials, and stage-audit only
  robot visual mesh bindings.
- Reuse `sample_uniform_bspline` and simulator-time association from
  `trajectory_review.py`.
- Preserve XYZ. The 3D projection must have equal metric scale and demonstrable
  Z sensitivity; no decorative lifting or GT planner input.
- Hash all presentation inputs and outputs and fail closed on missing,
  mismatched, non-finite, or undecodable artifacts.

## Success Signals

- The local diff is confined to owned paths.
- New unit tests cover first-view compatibility, external camera transforms,
  same-step alignment, material audit,
  H.264 stream parity, 3D Z sensitivity, provenance hashes, and malformed input.
- Targeted tests pass and legacy trajectory-review tests remain green.
- Gemini returns a concise list of changed files, tests and exact output, known
  limitations, and any assumptions needing Codex review.

## Failure Signals

- Any edit to immutable evidence or protected dirty files.
- A second simulation run presented as a synchronized view.
- An external camera not linked deterministically to the recorded robot state,
  or one that jumps/flips sides without a declared logged failure.
- XY-only rendering labeled 3D, Z exaggeration, decorative paths, or truth-fed
  planner content.
- Relaxed acceptance/safety thresholds or default behavior changes.
- Remote execution, commit, push, AC55 update, or completion claim.

## Return Format

```text
STATUS: READY_FOR_CODEX_REVIEW | BLOCKED
CHANGED_PATHS:
- ...
TESTS:
- command
  result
SCOPE_CHECK:
- immutable evidence unchanged: yes/no
- protected dirty paths untouched: yes/no
- remote execution performed: no
KNOWN_LIMITATIONS:
- ...
CODEX_REVIEW_NEEDED:
- ...
```

## Later Remote Sync Gate (Not Authorized In This Package)

After Codex approves the local diff, a separate gate will use SSH alias
`gpu5070ti`. It must compare local source hashes with both the Isaac execution
copy and any Foxy workspace copy before running, then copy all evidence back to
the same local paths. Expected artifacts are defined in `implement.md`. No
remote-only success may be reported.
