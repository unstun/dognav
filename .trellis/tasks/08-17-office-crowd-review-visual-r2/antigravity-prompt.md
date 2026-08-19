# Antigravity Execution Prompt — Office Crowd Review Visualization R2

You are implementing a narrowly scoped local Phase B change in the
`machine-dog-nav` repository. Work carefully and evidence-first. Do not expand
scope, hide failures, or claim acceptance on behalf of the human reviewer.

## Approved Start Gate

The active task is:

`/Users/sun/.codex/worktrees/164f/machine-dog-nav/.trellis/tasks/08-17-office-crowd-review-visual-r2`

Dr Sun explicitly approved the final plan on 2026-08-17, and the owning
Codex/Trellis session changed this task from `planning` to `in_progress`.
Before editing, verify `task.json` still reports `in_progress` and `task.py
current` resolves to this exact directory. Do not run `task.py start` yourself.
If either check differs, report `BLOCKED_TASK_STATE_MISMATCH` and stop.

## Mandatory Reading Order

1. `/Users/sun/.codex/worktrees/164f/machine-dog-nav/AGENTS.md`
2. `/Users/sun/.codex/worktrees/164f/machine-dog-nav/.trellis/workflow.md`
3. Active-task `prd.md`
4. Active-task `design.md`
5. Active-task `implement.md`
6. Active-task `research/verified-current-behavior.md`
7. `.trellis/spec/backend/quality-guidelines.md`, especially the sensor-rig,
   moving-obstacle, evidence-sync, and Office L0 crowd contracts
8. `.trellis/spec/guides/index.md`
9. `.trellis/spec/guides/code-reuse-thinking-guide.md`
10. `.trellis/spec/guides/cross-layer-thinking-guide.md`
11. `.pipeline/terminology/terminology.md`

Treat the local repository as the only source of truth. Verify current code,
tests, status, and hashes yourself; prior summaries are leads, not evidence.

## Phase B Objective

Implement opt-in Office human-review presentation support with all of the
following behavior:

1. Preserve the current candidate38/39 `closed_loop.mp4` camera composition and
   behavior exactly. Dr Sun calls this the first view. Do not replace it with a
   dog-head, cockpit, D435i, or robot-eye camera.
2. Add `closed_loop_third_person.mp4`: a genuinely external camera that follows
   smoothly beside the robot. Use one configured lateral side, explicit lateral
   distance, trailing bias, height, simulator-time smoothing, and bounded
   motion. Do not implement a fixed camera, orbit camera, implicit left/right
   flip, abrupt cut, or hidden second run.
3. Render both views after the same physics step without advancing simulation
   between renders. Record shared frame index, simulation step/time, physical
   root state, and each view's desired and realized eye/target pose in
   `camera_trace.jsonl`.
4. Make the full Lite3 visually distinguishable from the white Office floor and
   dark furniture using an opaque, non-emissive, Office-only review material
   override. Prefer a warm/orange torso and carrier with graphite limbs. Do not
   edit the URDF, meshes, collision, mass, inertia, joints, sensors, policy, or
   planner. Log every affected visual prim and unchanged physical identities.
5. Add a deterministic `1920x1080` four-panel review dashboard containing the
   preserved first view, synchronized external third-person view, a true 3D
   planned-versus-actual trajectory panel, and causal/event context.
6. The 3D panel must use recorded world XYZ from the active SCAN B-spline,
   physical Lite3 root path, and captured inflated occupancy. Reuse existing
   B-spline and simulator-time association helpers. Use equal metric scale,
   declare axes/units/time/trajectory ID, do not exaggerate Z, do not create a
   decorative lifted curve, and never feed ground truth into planning.
7. Add fail-closed presentation validation and provenance metadata: complete
   H.264/YUV420p decode, synchronized frame/rate/time parity, finite XYZ,
   non-zero Z sensitivity, camera-trace integrity, material-scope audit, and
   SHA-256 identity for every input and output.
8. Keep all new behavior default-off and preserve legacy non-Office behavior.

## Immutable and Protected Evidence

- Candidate38 and candidate39 are immutable evidence. Do not edit, replace,
  rename, delete, re-encode, relink, or reuse their result directories.
- Before implementation, record hashes for their MP4s, acceptance results,
  metrics, ROS events, and run identities, then confirm they remain unchanged.
- AC54 has passed. AC55 remains owned exclusively by Dr Sun. Do not check it,
  relabel it, claim full completion, or archive this task.
- Preserve every unrelated dirty or untracked file. Never clean, reset, stash,
  reformat, or stage another person's work.

## Allowed Modification Scope

- `integration/lite3_sim_bridge/lite3_sim_bridge/run_isaac_v12_fallback.py`
- `integration/lite3_sim_bridge/lite3_sim_bridge/trajectory_review.py` only for
  small backward-compatible reusable helpers
- one minimal new Office review presentation module under
  `integration/lite3_sim_bridge/lite3_sim_bridge/`
- matching tests under `integration/lite3_sim_bridge/tests/`
- `integration/lite3_sim_bridge/setup.py` only if a new entry point is necessary
- `.pipeline/experiments/2026-08-13_scan_foxy_isaac_closed_loop/run_remote_closed_loop.sh`
  only for default-off argument plumbing
- `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/run_remote_office_crowd.sh`
  only for default-off argument plumbing
- new task-owned local configuration/validation files
- this active Trellis task directory

## Forbidden Scope

- No changes to sibling `machine-dog`, robot assets, URDFs, meshes, checkpoint,
  SCAN behavior, controller semantics, safety thresholds, Office route,
  pedestrian schedule, or existing result directories.
- No SSH, remote sync, Isaac run, long run, candidate creation, training, or
  real-robot actuation in this phase.
- No commit, push, report/hot-memory update, acceptance checkbox, or archive.
- Do not silently repair an existing unrelated failure or reformat unrelated
  code.

## Required Local Validation

Run targeted tests:

```text
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest \
    integration.lite3_sim_bridge.tests.test_trajectory_review \
    integration.lite3_sim_bridge.tests.test_office_review_presentation
```

Run the full bridge test suite:

```text
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest discover \
    -s integration/lite3_sim_bridge/tests -p 'test_*.py'
```

Also run syntax/format/static checks already required by the repository for the
owned files, `git diff --check`, and a final path-scope audit. Save exact command
output to the new file
`.trellis/tasks/08-17-office-crowd-review-visual-r2/logs/antigravity-phase-b-tests.txt`
and save the structured return to
`.trellis/tasks/08-17-office-crowd-review-visual-r2/antigravity-phase-b-return.md`.
Create parent directories if needed; do not overwrite existing evidence.

## Success Conditions

- The diff is confined to allowed paths and candidate38/39 hashes are unchanged.
- Existing `closed_loop.mp4` behavior remains compatible by default.
- New side-follow camera math is deterministic, smoothly bounded, same-step,
  externally positioned, and covered by tests for no implicit side flip.
- Review material is visual-only and its scope is auditable.
- The 3D projection preserves real XYZ and tests prove Z changes display output.
- Targeted and full local tests pass with exact output recorded.
- No remote work or acceptance claim was performed.

If any condition fails, return `BLOCKED` with evidence. Do not broaden scope or
weaken a gate to make tests pass.

## Return Format

```text
STATUS: READY_FOR_CODEX_REVIEW | BLOCKED_TASK_STATE_MISMATCH | BLOCKED
CHANGED_PATHS:
- ...
TESTS:
- command: ...
  result: ...
SCOPE_CHECK:
- candidate38/39 unchanged: yes/no + hashes
- protected dirty paths untouched: yes/no
- remote execution performed: no
- commit/push performed: no
KNOWN_LIMITATIONS:
- ...
CODEX_REVIEW_NEEDED:
- ...
```

Stop after the Phase B return. Codex will independently review the complete
diff and rerun validation. Remote visual preflight requires a separate explicit
authorization from Dr Sun.
