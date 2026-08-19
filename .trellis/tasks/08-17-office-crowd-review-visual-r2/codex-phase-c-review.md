# Codex Phase C Independent Review — Gemini Round 1

## Verdict

`REJECTED_INCOMPLETE`

The delivered diff is a useful local prototype, but it does not satisfy Phase B
or authorize remote visual preflight. Keep the task `in_progress`; candidate38,
candidate39, AC54, and AC55 retain their existing meanings.

## Scope and Preservation

- Product changes are confined to owned paths:
  - `integration/lite3_sim_bridge/lite3_sim_bridge/run_isaac_v12_fallback.py`
  - new `integration/lite3_sim_bridge/lite3_sim_bridge/office_review_presentation.py`
  - new `integration/lite3_sim_bridge/tests/test_office_review_presentation.py`
- The pre-existing literature/result/survey/document dirty paths remain present
  and were not attributed to Gemini.
- Report-listed candidate38/39 acceptance, `metrics.jsonl`, and
  `ros_events.jsonl` hashes still match the frozen report.
- Every file currently present inside the candidate38/39 run directories has a
  latest modification time of `2026-08-17 10:08:47`, before Gemini's first
  product edit at `10:58:37`.
- The report-listed MP4s are not present at their candidate result paths in this
  checkout, so this review could not independently recompute those four MP4
  hashes. This is an evidence-availability limitation, not evidence of a change.
- Gemini did not create the required `antigravity-phase-b-return.md` or
  `logs/antigravity-phase-b-tests.txt`.

## Re-run Checks

```text
PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest \
  integration.lite3_sim_bridge.tests.test_trajectory_review \
  integration.lite3_sim_bridge.tests.test_office_review_presentation

Ran 34 tests in 0.541s — OK
```

```text
PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest discover \
  -s integration/lite3_sim_bridge/tests -p 'test_*.py'

Ran 113 tests in 0.482s — OK
```

`py_compile` and `git diff --check` also pass. These checks establish only that
the current helper-level implementation imports and its tests pass; they do not
establish the missing runtime behavior below.

## Blocking Findings

### P1 — Review material flag has no runtime implementation

`--office-review-material` is parsed, but no code reads it after parsing. The
material classifier, colour selector, and audit builder are called only by unit
tests. No USD material is defined or bound to robot visual prims, no stage audit
is written, and no physical/runtime identity comparison is recorded. The robot
will therefore remain visually unchanged.

### P1 — No dashboard renderer or run-data ingestion exists

The new module ends after an isometric projection helper and a metadata-dict
builder. It does not read `ros_events.jsonl`, `metrics.jsonl`, camera trace, or
the two raw MP4s; it does not reuse the existing B-spline/time-association
helpers; and it does not draw or encode the required four-panel 1920x1080
dashboard. No output path, entry point, shell integration, or hash manifest is
implemented.

### P1 — Presentation validators fail open

Direct Codex reproductions show:

```text
wrong_codec_probe -> passed=True for codec=mpeg4
rate_mismatch     -> passed=True for 25 fps versus 30 fps
missing_trace_fields -> passed=True for a row with no poses, step, time, or root state
```

`validate_video_decodable()` only runs `ffprobe` and returns PASS for any video
stream; it does not require H.264/YUV420p or perform full decode.
`validate_stream_parity()` ignores frame rate. `validate_camera_trace()` treats
missing required fields as optional and does not verify simulator time, step
alignment, or bounded realized camera motion.

### P1 — Side-follow motion is not bounded or freezeable

The camera uses hard-coded module defaults rather than explicit CLI/effective
input fields. Its exponential interpolation has no maximum translation/target
rate. A direct test moving the desired eye by 1000 m with `dt=1` and rate `4`
moves the realized camera by `981.684 m` in one update, despite the requirement
for bounded motion. Invalid/non-positive `dt` returns the desired pose directly,
which is another teleport path. No runner-level test proves preserved first-view
equations, same-step dual rendering, or lack of side flips in recorded output.

### P1 — Runtime packaging and fail-closed argument contracts are missing

Neither Office nor core remote launcher passes the new flags or records the new
module/config in effective input and source hashes. The runner does not reject a
third-person path without a primary video/trace, or a trace path without a
third-person stream. It can therefore silently produce no third-person evidence
or an empty trace while the existing qualification report remains otherwise
eligible to pass.

## Required Gemini Revision

1. Implement and stage-audit the actual Office-only robot visual-material
   binding; add unchanged physical/sensor identity evidence.
2. Implement a real deterministic dashboard renderer/CLI that consumes and
   hashes the declared run artifacts and preserves true XYZ/time provenance.
3. Replace helper-only checks with one fail-closed aggregate presentation
   validator; require full H.264/YUV420p decode, rate/resolution/frame parity,
   complete trace schema, monotonic step/time, and bounded motion.
4. Expose and validate side-camera configuration, add explicit motion limits,
   include it in run identity/effective input, and test runner integration.
5. Wire default-off flags, outputs, source hashes, and validation into the
   task-owned launch/package path without altering frozen navigation inputs.
6. Add the required Phase B raw test log and structured return, then stop for a
   new Codex review. Do not run remote Isaac or create a candidate.
