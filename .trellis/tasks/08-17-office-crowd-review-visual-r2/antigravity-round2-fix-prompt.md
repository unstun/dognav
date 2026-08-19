# Antigravity / Gemini Round 2 Fix Prompt

You are continuing the active `machine-dog-nav` task after Codex rejected the
first implementation as incomplete. This is a repair round, not a new design
round. Implement the missing runtime behavior, run the complete local checks,
and stop for a second Codex review.

## Repository and Active Task

- Repository and only code source of truth:
  `/Users/sun/.codex/worktrees/164f/machine-dog-nav`
- Active task:
  `.trellis/tasks/08-17-office-crowd-review-visual-r2`
- The task is already `in_progress`. Do not run `task.py start` again.

Before editing, read completely and in order:

1. `AGENTS.md`
2. `.trellis/workflow.md`
3. active-task `prd.md`
4. active-task `design.md`
5. active-task `implement.md`
6. active-task `research/verified-current-behavior.md`
7. active-task `codex-phase-c-review.md`
8. `.trellis/spec/backend/index.md`
9. `.trellis/spec/backend/quality-guidelines.md`
10. `.trellis/spec/guides/index.md`
11. `.trellis/spec/guides/code-reuse-thinking-guide.md`
12. `.trellis/spec/guides/cross-layer-thinking-guide.md`
13. `.pipeline/terminology/terminology.md`

Inspect the current diff and preserve the useful Round 1 work. Do not trust the
green helper tests as proof that runtime behavior exists. Search for existing
rendering, B-spline sampling, event-time mapping, hashing, USD material, and
packaging helpers before adding new code.

## Frozen Boundaries

- Candidate38 and candidate39 are immutable. Do not edit, relink, re-encode,
  rename, delete, copy over, or reuse either result directory.
- Preserve every unrelated dirty/untracked path. Do not reset, clean, stash,
  reformat, stage, or commit other work.
- Keep `closed_loop.mp4` camera equations and behavior unchanged. This is Dr
  Sun's first view. Never replace it with a D435i, dog-head, cockpit, or
  robot-eye camera.
- Do not change the URDF, meshes, collision, mass, inertia, joints, checkpoint,
  policy, sensors, SCAN planner/controller, Office route, pedestrian schedule,
  safety thresholds, AC54, or AC55.
- No SSH, remote sync, Isaac run, dry run, candidate generation, training,
  real-robot actuation, commit, push, archive, report update, or hot-memory
  update in this round.
- The local repository is the only source of truth. A remote-only edit or
  result would be invalid, but remote work is not authorized here anyway.

## Round 2 Required Work

### 1. Implement the actual Office review material binding

The current `--office-review-material` flag is dead. Make it perform a real
runtime change only when Office review mode is explicitly enabled:

- After the Lite3 USD is instantiated, discover actual visible
  `UsdGeom.Mesh` prims under the robot root. Do not operate on collision,
  physics, sensor, or unrelated scene prims.
- Define opaque, non-emissive review materials and bind warm/orange to the
  torso/carrier and graphite to the limbs. Keep opacity exactly `1.0` and
  emissive color zero.
- Fail closed if the flag is enabled but no eligible robot visual meshes are
  found or a non-visual/non-robot prim would be affected.
- Write a run-owned `office_review_material_audit.json` containing every
  affected prim path, classification, bound material/color, opacity/emission,
  the unchanged robot asset/referenced-mesh hashes, and before/after physical,
  collision, joint, and sensor-target inventories or their deterministic
  identities.
- Wire the audit into `runtime_composition.json`, `run_identity.json`, the
  qualification report, and output hashing. Do not merely create another pure
  dictionary helper that is never called.
- Keep USD/Isaac imports behind the runtime boundary so local unit tests can use
  small mocks/fakes without requiring Isaac Sim.

### 2. Make the side camera configurable, deterministic, and truly bounded

Keep the external smooth side-follow design, but complete its contract:

- Add explicit, validated default-off CLI/config fields for side, lateral
  distance, trailing bias, height, look-ahead, look-height, smoothing rate,
  maximum eye translation speed, and maximum target translation speed.
- Accept only finite values; require positive distances/rates as appropriate;
  require side to be exactly one declared left/right value. Reject invalid
  values before simulator startup.
- Replace the current unbounded interpolation with deterministic simulator-time
  smoothing plus a vector displacement clamp of `max_speed * dt` for both eye
  and target. Non-positive/non-finite `dt` or rates must fail closed rather than
  teleport to the target.
- First initialization may set the first realized pose directly because there
  is no previous frame; all later frames must satisfy the declared bounds.
- Record the complete frozen camera config in effective input, run identity,
  runtime composition, qualification report, camera trace, and input hashes.
- Move reusable imports out of the per-frame loop.
- Add runner-level tests proving: the legacy first-view equations stay
  unchanged; both renders occur at one simulation step with no `env.step`
  between them; camera trace indices/steps/times match both writers; side never
  flips; and realized per-frame motion stays within the configured limits.

### 3. Enforce fail-closed option combinations

When Office review presentation is enabled, require all of these together:

- primary `--video-path`;
- third-person output path;
- camera-trace output path;
- review material flag;
- complete finite side-camera configuration.

Reject partial combinations, non-Office use, identical primary/third output
paths, paths inside candidate38/39, and output files that already exist. Do not
silently create an empty trace or omit the third-person stream while allowing a
PASS report.

### 4. Implement a real deterministic four-panel dashboard renderer

The current module has only projection and metadata helpers. Add a real
post-run renderer/CLI that:

- reads and hashes the preserved first-view MP4, third-person MP4,
  `camera_trace.jsonl`, `ros_events.jsonl`, Isaac `metrics.jsonl`, and
  `run_identity.json`;
- reuses `trajectory_review.py` B-spline sampling and simulator-time mapping
  instead of duplicating them;
- extracts the active SCAN B-spline in world XYZ, accumulated physical root XYZ,
  and captured inflated-occupancy XYZ with a deterministic recorded downsample;
- renders a real `1920x1080` H.264/YUV420p dashboard with four labeled panels:
  preserved first view, synchronized external third view, equal-scale
  isometric 3D plan/actual/occupancy, and causal/event context;
- shows axes, metres, simulator time, active trajectory ID, and legend; uses Z
  without exaggeration and never creates a decorative lifted curve;
- keeps ground-truth pedestrian data clearly labeled as evaluation context and
  never substitutes it for captured SCAN occupancy;
- writes dashboard metadata containing input/output SHA-256, frame-to-simulator
  mapping, projection parameters, XYZ bounds, trajectory identities,
  occupancy-sampling rule, codec/pixel format/resolution/rate/frame count, and
  claim boundary;
- never overwrites an existing output.

Add a small synthetic end-to-end test fixture that creates two tiny videos plus
camera/ROS/metrics inputs, runs the real renderer, fully decodes the resulting
dashboard, and verifies that changing real input Z changes the rendered 3D
panel and metadata. Tests must exercise the actual CLI/entry point, not only the
same helper that they assert.

### 5. Replace fail-open helpers with one aggregate presentation validator

Implement a fail-closed validator/CLI used by packaging:

- Fully decode every frame of both raw streams and the dashboard, not just
  `ffprobe` headers.
- Require codec `h264`, pixel format `yuv420p`, positive dimensions/frame count,
  declared resolution, equal rational frame rate, equal raw-stream resolution,
  and equal raw-stream frame count.
- Parse every camera trace row with one owned schema/normalizer. Require exactly
  the declared fields and vector lengths, finite values, frame indices starting
  at zero, monotonic simulation steps/times, same-run identity, constant side,
  and bounded realized motion.
- Require finite non-empty plan/root/occupancy XYZ from the declared sources,
  real Z provenance, deterministic occupancy sampling, input/output hashes, and
  exact metadata identity.
- Ensure presentation failure can only fail the result; it may never convert an
  existing Office automated FAIL into PASS or satisfy AC55.

Add negative tests that must fail for:

- MPEG-4/non-H.264 video;
- non-YUV420p video;
- corrupt/truncated video;
- 25 fps versus 30 fps;
- missing or extra trace fields;
- missing root pose, step, simulator time, or camera pose;
- non-monotonic time/step;
- side flip or excessive camera motion;
- missing/non-finite XYZ;
- XY-only/decoratively lifted data;
- hash mismatch or existing output overwrite.

The following Round 1 reproductions must no longer pass:

```text
wrong_codec_probe -> passed=True for codec=mpeg4
rate_mismatch -> passed=True for 25 fps versus 30 fps
missing_trace_fields -> passed=True with no poses/step/time/root
unbounded_one_second_move_m -> 981.6843611112657
```

### 6. Wire local packaging and launch inputs, still default-off

- Add the smallest task-owned argument plumbing to
  `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/run_remote_office_crowd.sh`
  and, only if genuinely shared, the core closed-loop launcher.
- Record every presentation option and output path in `effective_input.txt`.
- Include the new module, relevant runner/launcher sources, config, validator,
  and renderer in `input_sha256.txt`/output manifests.
- Invoke dashboard rendering and aggregate validation only after the live
  simulation boundary. A presentation validation failure must produce a
  non-success packaging/launcher result without changing navigation metrics.
- Preserve all legacy behavior when the new review mode is disabled.
- Do not create or reserve candidate40 in this local round.

### 7. Complete tests and the required return artifacts

At minimum, independently run:

```text
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest \
    integration.lite3_sim_bridge.tests.test_trajectory_review \
    integration.lite3_sim_bridge.tests.test_office_review_presentation
```

```text
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest discover \
    -s integration/lite3_sim_bridge/tests -p 'test_*.py'
```

Also run:

- `python3 -m py_compile` on every changed Python file;
- `bash -n` on every changed shell file;
- `git diff --check`;
- a changed-path audit against `implement.md` Owned Paths;
- immutable candidate38/39 hash/mtime checks available in this checkout.

Save exact, unabridged command output to:

`.trellis/tasks/08-17-office-crowd-review-visual-r2/logs/antigravity-round2-tests.txt`

Save the structured return to:

`.trellis/tasks/08-17-office-crowd-review-visual-r2/antigravity-round2-return.md`

## Allowed Modification Scope

Only the Owned Paths in the active task `implement.md`, including the task
directory for the new log/return. Do not modify the parent report, hot memory,
candidate result directories, unrelated literature/surveys/docs, or sibling
repositories.

## Success Signals

- All five P1 findings in `codex-phase-c-review.md` are resolved in runtime and
  test code, not hidden or relabeled.
- The material flag changes actual robot visual meshes and produces an audit.
- The real dashboard CLI produces and validates a four-panel MP4 from synthetic
  recorded inputs.
- The negative validator fixtures fail for the intended reason.
- Side-camera motion is configurable, recorded, and mathematically bounded.
- Default-off legacy behavior and the preserved first view remain unchanged.
- Targeted/full tests and static checks pass with raw logs.
- Candidate38/39 and unrelated dirty paths remain untouched.
- No remote execution or acceptance claim occurred.

## Failure Signals

- Adding more unused helpers or tautological tests without runtime integration.
- A green test suite while material/dashboard/validator/launcher paths remain
  unreachable.
- Any fail-open missing evidence, truth-fed planning, threshold relaxation,
  candidate modification, remote run, commit/push, AC55 update, or completion
  claim.

If blocked by Isaac-only APIs, implement and locally test the pure/stage-adapter
boundary, record the exact missing runtime proof, and return `BLOCKED`; do not
fake a runtime PASS.

## Required Return Format

```text
STATUS: READY_FOR_CODEX_REVIEW | BLOCKED
RESOLVED_FINDINGS:
- P1 material binding: ...
- P1 dashboard renderer: ...
- P1 fail-closed validation: ...
- P1 bounded/frozen side camera: ...
- P1 launch/package contract: ...
CHANGED_PATHS:
- ...
TESTS:
- command: ...
  result: ...
NEGATIVE_REPRODUCTIONS:
- wrong codec: rejected yes/no + reason
- fps mismatch: rejected yes/no + reason
- incomplete trace: rejected yes/no + reason
- excessive motion: rejected yes/no + reason
SCOPE_CHECK:
- candidate38/39 unchanged: yes/no + evidence
- protected dirty paths untouched: yes/no
- remote execution performed: no
- commit/push performed: no
KNOWN_LIMITATIONS:
- ...
CODEX_REVIEW_NEEDED:
- ...
```

Stop after producing the Round 2 log and return. Codex will independently
review the complete diff and rerun all checks before any remote authorization.
