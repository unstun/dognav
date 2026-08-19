# Codex Round 3 Independent Review

- **Task:** `08-17-office-crowd-review-visual-r2`
- **Date:** 2026-08-17
- **Stage:** `experiment + analysis`
- **Reviewed return:** `antigravity-round3-return.md`
- **Decision:** `REJECTED_INCOMPLETE`
- **Remote preflight:** not authorized
- **Task status:** remains `in_progress`
- **Human gate:** AC55 remains pending Dr Sun

## Executive conclusion

The Round 3 implementation does not satisfy the approved quality/multi-view
prompt and must not be used to launch a new candidate. The local unit suites are
green, but the real runner path contains a deterministic `TypeError`, the raw
camera streams remain 1280x720, the Office launcher does not enable or record
the review pipeline, and the aggregate validator is still fail-open for several
mandatory quality and provenance gates.

No remote Isaac run, candidate generation, formal training, or real-robot
actuation was performed during this review.

## Blocking findings

### P1-1 — The real Office review runner crashes before material capture

`run_isaac_v12_fallback.py:3527-3533` calls
`apply_office_review_material_usd(..., pre_inventory=pre_inventory)`, but the
function signature at `office_review_presentation.py:631-636` has no
`pre_inventory` parameter.

Direct reproduction:

```text
TypeError: apply_office_review_material_usd() got an unexpected keyword argument 'pre_inventory'
```

The synthetic tests call the function without this runner-only keyword and
therefore do not cover the failing integration path.

### P1-2 — The promised 1920x1080 high-quality raw streams are not wired

The runner still freezes `VIDEO_RESOLUTION = (1280, 720)` at
`run_isaac_v12_fallback.py:93`, then assigns that resolution to the Office
viewer at lines 1719-1733. All three raw writers use the same generic imageio
configuration at lines 3676-3708; no raw-stream high-profile/CRF/color-metadata
contract is enforced.

`FROZEN_QUALITY_PROFILE` declares 1920x1080 and H.264 High in the presentation
module, but it is never consumed by the runner or validator. Only the composed
dashboard is 1920x1080.

The claimed opt-in lighting implementation is also absent. The parser exposes
`--office-review-lighting-profile`, `--office-review-dome-light-intensity`, and
`--office-review-exposure`, defaults the profile to `high_contrast`, and no
runtime code reads those values. The scene dome light remains hard-coded to
900.0. This contradicts the return's claim that review lighting is disabled by
default and wired through separate flags.

### P1-3 — The Office launcher and effective input are not connected

The only launcher change is adding `office_review_presentation.py` to
`input_sha256.txt`. The actual invocation at
`run_remote_closed_loop.sh:397-418` still passes only the original
`--video-path`, FPS, and stride. It does not pass the presentation flag, side
video, overview video, trace, material audit, dashboard, or metadata paths.

`effective_input.txt` also contains none of the new camera, render, material,
lighting, or output settings. Therefore the intended Office remote entry point
cannot produce the package described by the return, and its identity cannot
reconstruct the claimed review configuration.

### P1-4 — The validator accepts disallowed encoding and copied camera content

The validator checks only `codec_name == h264`, `pix_fmt == yuv420p`, raw
resolution, and equality of the three raw rational frame-rate strings. It does
not enforce minimum 25 fps, H.264 High profile, color metadata, dashboard FPS
parity, or the frozen quality profile.

Independent reproduction from the current code:

```text
counterexample_12fps_baseline_passed= True
raw_r_frame_rate= 12/1 profile= Constrained Baseline
issues= []
```

Camera distinction is checked only by file SHA-256. Re-encoding the primary
stream twice produced three different files whose decoded first frames were
pixel-identical; the validator still passed:

```text
counterexample_same_visual_views_passed= True
first_frame_mae_first_side= 0.0
first_frame_mae_first_overview= 0.0
issues= []
```

The full decode helper uses OpenCV until `read()` returns false. It is not an
error-sensitive ffmpeg decode and does not reconcile decoded frames with the
ffprobe frame count, so the approved truncated/corrupt-media gate is also not
implemented as specified.

### P1-5 — Provenance, trace, and material checks remain fail-open

The API has ten paths, but the approved prompt also requires the effective
input and acceptance/config identity. Neither is a validator input or a
dashboard metadata hash. The trace's common `run_identity` is never compared
with `run_identity.json.config_sha256`, there is no shared state-snapshot
identity, steps are allowed to repeat, and eye speed is checked while target
speed and recorded displacement fields are not.

The material validator trusts `physics_inventory_unchanged: true`, rejects only
paths containing `floor` or `office`, and does not enforce robot-root scope,
opacity, emission, non-empty/equal inventories, or asset/reference hashes. The
real USD inventory query never appends body paths and omits the required mass,
inertia, joint-kinematic, and sensor-rig state.

One combined counterexample changed all of the following while still receiving
`passed=True`: a fabricated robot-subtree material record with opacity 0.2 and
emission 9.0, empty copied inventories, a run-identity JSON that disagreed with
the trace, a repeated step, and a final side-camera target teleport to
`[999, 999, 999]`.

```text
counterexample_fabricated_identity_equal_step_target_teleport_passed= True
issues= []
```

### P1-6 — The green tests do not establish the claimed gates

The independently rerun suites do pass:

```text
targeted: Ran 32 tests in 8.173s — OK
full bridge: Ran 111 tests in 8.489s — OK
py_compile: PASS
bash -n launcher: PASS
git diff --check: PASS
```

However, no test exercises the runner's material call, launcher argument
construction, effective-input contents, actual 1920x1080 raw capture, minimum
FPS/profile, decoded visual distinction, or identity binding. In addition,
`test_reproduction_overwrite_forbidden` at
`test_office_review_presentation.py:486-500` renders once but contains no second
call and no assertion, so it cannot prove the overwrite rejection claimed by
the return.

## Verified partial improvements

- Side-follow and elevated overview pose helpers exist and use bounded smoothing.
- The multi-camera loop renders after one physics-state snapshot and contains no
  additional `env.step()` between views.
- The dashboard itself uses a direct ffmpeg rawvideo-to-libx264 pipe at
  1920x1080 and does not intentionally overwrite existing outputs.
- Empty events/metrics and literal candidate38/candidate39 output paths are
  rejected by the currently tested code paths.

These are partial implementation results only; they do not authorize remote
execution or candidate promotion.

## Immutable evidence check

The locally available candidate38/39 evidence still matches the frozen hashes:

```text
candidate38 closed_loop.mp4              010acee0275475a2bd3661f6db7743adb64be25cc4fcaa3e9fe8ac04a00bed31
candidate38 office_crowd_acceptance.json b6a759cdf54a42c95a84634d338592d27819989c6c99a92430f05d4b57afffad
candidate38 ros_events.jsonl             7b15be33b15ebfb84a2c2b594114bf365c2cdfa33d7236695b57ae24de346546
candidate39 closed_loop.mp4              4553f0384697e41c372d6dcfb77b50373a4d5832d57d5d4187487fb6775063c9
candidate39 office_crowd_acceptance.json 8b4f235d172ca6b42dc62ef417699ff6427e939f455db792bc0451c0884d9ca2
candidate39 ros_events.jsonl             1b554788f3eaf18cda67c9bccf90418f6b8d9c542044ecff5983fd7a314e2630
```

The MP4 mtimes in the local source-of-truth checkout remain 2026-08-17 08:44:07
for candidate38 and 2026-08-17 08:48:54 for candidate39, predating the Round 3
return. No protected candidate file was written by Codex.

## Required next action

Return this review to Gemini for a fourth local-only repair round. Do not start
remote preflight and do not create a new candidate until every P1 above is
closed by runner/launcher-level tests and the independent counterexamples all
report `passed=False`. AC55 remains exclusively Dr Sun's decision after a new,
validated, immutable candidate is actually produced and viewed.
