# Antigravity Round 3 — Office L0 High-Quality Multi-View Remediation

You are the implementation agent for the third local remediation round of the
`machine-dog-nav` Office L0 crowd human-review presentation.

## 1. Stage, Source of Truth, and Current Decision

- Current stage: `experiment + analysis`.
- Local source of truth:
  `/Users/sun/.codex/worktrees/164f/machine-dog-nav`
- Active Trellis task:
  `.trellis/tasks/08-17-office-crowd-review-visual-r2`
- Codex Round 2 decision: `REJECTED_INCOMPLETE`.
- AC54 remains the previously passed automated gate for immutable candidates
  38 and 39.
- AC55 remains human-owned and pending. You may not set, claim, or imply AC55.
- Dr Sun has now explicitly rejected the existing visual quality: the Office
  video is less readable than the earlier forest evidence. The new work must
  improve source rendering, robot/background contrast, motion smoothness, and
  camera coverage rather than merely re-encode the old evidence.

The local repository is the only code truth. Do not leave final code or task
state only in another workspace. Every accepted code change must be visible in
the local `git diff` at the same repository paths.

## 2. Read Before Editing

Read these files completely and in order:

1. `AGENTS.md`
2. `.trellis/workflow.md`
3. `.trellis/tasks/08-17-office-crowd-review-visual-r2/prd.md`
4. `.trellis/tasks/08-17-office-crowd-review-visual-r2/design.md`
5. `.trellis/tasks/08-17-office-crowd-review-visual-r2/implement.md`
6. `.trellis/tasks/08-17-office-crowd-review-visual-r2/research/verified-current-behavior.md`
7. `.trellis/tasks/08-17-office-crowd-review-visual-r2/codex-phase-c-review.md`
8. `.trellis/tasks/08-17-office-crowd-review-visual-r2/codex-round2-review.md`
9. `.trellis/spec/backend/index.md`
10. `.trellis/spec/backend/quality-guidelines.md`
11. `.trellis/spec/guides/index.md`
12. `.trellis/spec/guides/code-reuse-thinking-guide.md`
13. `.trellis/spec/guides/cross-layer-thinking-guide.md`
14. `.pipeline/terminology/terminology.md`

Treat the two Codex review reports as executable defect reports. Do not trust
the previous Antigravity return's claim that all five P1 items were resolved.

## 3. This Round's Goal

Produce a locally reviewable, default-off implementation for one future Office
L0 run that records three synchronized, independently openable camera videos
and one truthful 3D evidence dashboard:

1. `closed_loop.mp4`
   - Preserve the existing candidate38/39 chase-camera composition and camera
     equations exactly.
   - This is Dr Sun's user-facing “first-person” view even though it is a chase
     camera.
   - Do not replace it with a D435i, robot-head, cockpit, or literal optical
     frame view.

2. `closed_loop_third_person_side.mp4`
   - A genuine external, smooth lateral side-follow observer.
   - It must show the complete articulated Lite3, nearby official pedestrians,
     clearance, gait, and route context.
   - It must remain on one configured side and must not orbit or flip sides.

3. `closed_loop_overview.mp4`
   - A separate elevated wide overview camera, not a renamed copy of either
     other view.
   - It must show the robot, nearby pedestrians, local route context, and enough
     surrounding Office geometry to understand avoidance and replanning.
   - It may follow the robot slowly, but must remain visibly external and use
     bounded simulator-time motion.

4. `office_review_dashboard.mp4`
   - A synchronized multi-view review dashboard containing the three camera
     views, a real world-XYZ planned-versus-actual trajectory panel, and causal
     event context.
   - The three raw camera MP4s remain the primary full-resolution evidence and
     must never be replaced by dashboard-sized panels.

This round is local implementation and testing only. Do not run remote Isaac,
do not create a preflight or candidate, and do not claim that real videos were
generated. Stop for Codex review first.

## 4. Immutable and Forbidden Boundaries

1. candidate38 and candidate39 are immutable evidence.
2. Do not edit, replace, move, rename, re-encode, touch, or delete any artifact
   under candidate38 or candidate39.
3. Do not create candidate40 or reserve any candidate name.
4. Do not change AC54, AC55, parent reports, hot memory, or archived state.
5. Do not run SSH, remote Isaac, GPU jobs, training, dry runs, preflights, formal
   candidates, or real-robot actuation.
6. Do not commit, push, archive, or rewrite Git history.
7. Preserve all existing dirty and untracked files. Do not revert other work.
8. Do not change the Lite3 URDF, meshes, collision geometry, mass, inertia,
   joints, checkpoint, policy, observation, controller, sensor, SCAN planner,
   Office route, pedestrians, schedule, or frozen automated thresholds.
9. Do not use pedestrian ground truth as planner input or trajectory data.
10. All new behavior must be opt-in and disabled by default.

## 5. Source-Quality Contract for All Three Raw Videos

The old Office files are only 1280x720 at 12 fps. The next run must not repeat
that capture contract.

Implement and validate a frozen review-quality profile with:

- native output resolution: exactly `1920x1080` for every raw camera stream;
- capture rate: at least `25 fps`, with `30 fps` preferred when it is an exact
  deterministic divisor of the simulator capture cadence;
- identical exact rational frame rate on all three streams;
- identical frame count and captured simulator-step sequence;
- H.264 High profile and `yuv420p`;
- one-generation encoding from rendered RGB frames to the raw H.264 output;
- no OpenCV `mp4v` staging for any raw camera stream;
- no frame interpolation, duplication, optical flow, or AI upscaling;
- no silent resize from a lower-resolution render product;
- no post-hoc sharpening presented as native detail;
- fixed renderer, anti-aliasing, render scale, exposure, tone-mapping, and
  motion-blur settings recorded in effective input and run identity.

Use a quality-oriented H.264 configuration such as direct libx264 CRF 14–16
with a declared preset, or an equivalently audited encoder. Do not enforce a
misleading arbitrary bitrate as the only quality gate. Record codec, profile,
pixel format, CRF/CQ, preset, color range, color primaries, transfer, matrix,
resolution, exact rational rate, and frame count.

If Isaac's supported renderer settings differ from the proposed names, use the
official runtime API actually available in the pinned Isaac version. Do not
invent unsupported Carb settings. Isolate Isaac-only imports so local tests
remain runnable.

Dashboard encoding may decode the three raw MP4s, but it must use one explicit
high-quality H.264 encode and must not be fed through an MP4V intermediate.

## 6. Robot Legibility and Lighting

The existing Office video washed a light grey/white Lite3 into a white tiled
floor under a strong dome light. Fix the source presentation rather than merely
raising saturation during post-processing.

### 6.1 Material binding

After the Lite3 USD is instantiated:

1. Find eligible visible `UsdGeom.Mesh` prims strictly under the robot root.
2. Explicitly exclude collision-only, invisible, proxy, sensor-raycast-only,
   Office-scene, pedestrian, and non-robot prims.
3. Apply a bright warm orange, opaque, non-emissive material to torso/carrier
   visual meshes.
4. Apply a dark graphite, opaque, non-emissive material to articulated limbs
   and joint housings.
5. Use `opacity=1.0`, emission/emissive color equal to zero, and documented
   roughness/metallic values.
6. Fail if no eligible visible robot meshes are found.
7. Fail if an affected prim is outside the exact robot subtree.
8. Fail if any affected prim is a collision-only or invisible prim.

### 6.2 Real before/after audit

Do not copy the pre-inventory dictionary and call it a post-inventory.

Implement a reusable stage/runtime inventory function and invoke it both before
and after material binding. It must independently re-query and record:

- body/link identities and counts;
- joint identities, types, and counts;
- collision prim paths and counts;
- mass and inertia identities/values;
- sensor target identities;
- robot visual mesh paths and visibility;
- robot asset and referenced-mesh SHA-256 values.

The audit passes only when the independently measured physical, collision,
joint, mass/inertia, and sensor inventories are equal before and after, while
the eligible visual-material bindings change as declared.

Write `office_review_material_audit.json` with the full affected prim list,
classification, material path, color, opacity, emission, before/after
inventories, robot hashes, and explicit claim boundary.

### 6.3 Lighting/exposure

Add a review-only, default-off Office lighting profile. It must preserve scene
geometry and physics and aim for readable mid-tones, shadows, and robot/floor
separation. Record all light intensities, colors, exposure, tone mapping, and
renderer settings. Do not use emission, transparency, hidden geometry, or fake
outlines to simulate visibility.

## 7. Synchronized Multi-Camera Runtime Contract

For each captured frame:

```text
one completed physics step
  -> read one immutable root state snapshot
  -> set and render preserved chase view
  -> set and render side-follow view
  -> set and render overview view
  -> append all three frames
  -> append one shared multi-view trace row
  -> only then allow the next physics step
```

Hard requirements:

- No `env.step()`, simulator-time advance, command consumption, robot-state
  mutation, or pedestrian advance between the three renders.
- Do not run the simulation three times.
- Do not splice frames from different attempts.
- Set the intended camera pose immediately before every render so camera state
  cannot leak from one view into the next frame.
- Cache imports and validated configurations outside the per-frame loop.
- Close all three writers and the trace deterministically on success or error.
- A writer or trace failure fails presentation packaging but must not rewrite
  the navigation metrics.

### 7.1 Side-follow camera

Expose and validate:

- `side` (`left` or `right`);
- lateral distance;
- trailing bias;
- eye height;
- target look-ahead;
- target height offset;
- smoothing rate;
- maximum eye speed;
- maximum target speed.

Use simulator-time smoothing plus vector displacement clamps:

- `eye_delta <= max_eye_speed * dt`
- `target_delta <= max_target_speed * dt`

The first frame may initialize directly. Every later frame must be bounded.
Reject non-finite or non-positive `dt`, rate, and speed limits. Never teleport
on invalid timing.

### 7.2 Overview camera

Expose a separate validated configuration for:

- azimuth/diagonal offset;
- horizontal follow distance;
- elevation/height;
- look-at offset;
- field of view if the runtime supports it;
- smoothing rate;
- maximum eye and target speeds;
- robot-centred follow window or declared fixed-scene mode.

The overview must be clearly different from the chase and side views. It must
not silently collapse to either pose. It must keep the robot and local crowd
context visible without excessive top-down flattening.

### 7.3 Shared camera trace

Write one `camera_trace.jsonl` row per captured simulator step containing:

- schema version;
- frame index starting at zero and continuous;
- physics step and finite strictly increasing simulator time;
- one common non-empty run identity;
- root position and quaternion;
- exact renderer/capture settings;
- for every view: configured pose parameters, desired eye/target, realized
  eye/target, `dt`, displacement, maximum allowed displacement, fallback reason;
- one shared state-snapshot identity proving all three renders used the same
  root state.

The preserved chase view may record its existing occlusion fallback, but the
fallback must remain explicit and must not be applied to the other views.

## 8. Fail-Closed CLI and Output Creation

When multi-view review mode is enabled, require all of these paths:

- primary chase video;
- side-follow video;
- overview video;
- camera trace;
- material audit;
- dashboard video;
- dashboard metadata;
- presentation validation report.

Also require the complete side and overview camera configurations and the
quality profile.

Reject:

- partial flag combinations;
- non-Office courses;
- duplicate or aliasing paths;
- any candidate38/39 target;
- any existing file, directory, symlink, or resolved alias at an output path;
- output paths nested inside any existing immutable candidate;
- non-finite or out-of-range quality/camera parameters.

Remove `overwrite`, `--overwrite`, and every code path that permits replacement.
The Isaac runner must never call a renderer with overwrite enabled. Use fresh
paths and exclusive creation. Temporary staging paths must also be unique and
must not overwrite prior evidence.

## 9. Truthful 3D Multi-View Dashboard

Read and hash all mandatory inputs:

- all three raw camera MP4s;
- camera trace;
- material audit;
- `ros_events.jsonl`;
- `metrics.jsonl`;
- `run_identity.json`;
- effective input;
- relevant acceptance/config identity.

The dashboard must include:

- all three synchronized camera views;
- active SCAN planned B-spline in genuine world XYZ;
- accumulated physical Lite3 root trajectory in genuine world XYZ;
- genuine captured SCAN inflated-occupancy XYZ with deterministic downsampling;
- causal/event information derived from recorded data.

Use the existing `trajectory_review` B-spline sampler and simulator-time
association. Do not catch a malformed plan and silently substitute a different
schema. Malformed or absent plan timing must fail.

The dashboard may use 2560x1440 if needed to keep all panels readable; record
the frozen layout and exact resolution. Do not shrink the raw evidence files.
The 3D panel must have metrically equal axes, world-frame labels, units,
trajectory ID, time, legends, provenance, and no Z exaggeration. Do not lift XY
data decoratively. Pedestrian ground truth remains evaluation-only context.

Never synthesize status claims. In particular:

- do not hard-code collision `PASS`;
- do not hard-code zero watchdog events;
- do not claim four-foot support from a default value;
- do not substitute zeros when mandatory metrics are absent.

Render the recorded value and its source. If a non-required display value is
unavailable, show `unknown`; if a required evidence value is unavailable, fail.

Metadata must record:

- every mandatory input SHA-256;
- output SHA-256;
- exact layout;
- codec/profile/pixel format/color metadata;
- resolution/rational frame rate/frame count;
- capture and renderer settings;
- frame-to-simulator-time mapping;
- plan/root/occupancy provenance and non-empty sample counts;
- XYZ bounds and real Z source;
- trajectory IDs;
- deterministic occupancy sampling algorithm, maximum count, seed, and result;
- source hashes for runner, renderer, validator, launchers, and configs;
- claim boundary.

## 10. Aggregate Validator

All arguments are mandatory. The CLI may not omit ROS events, metrics, run
identity, effective input, material audit, or acceptance/config identity.

Fail closed unless all of the following hold:

1. All three raw videos and the dashboard fully decode with an error-sensitive
   decoder command, not merely a header probe or OpenCV EOF loop.
2. Codec/profile/pixel format/resolution/rational fps/frame count match the
   frozen quality profile.
3. Decoded frame count equals the declared frame count for every video.
4. The three raw streams have the same frame count, exact rational rate, and
   captured simulator-step sequence.
5. The three raw files have distinct hashes and measurably distinct image
   content; a copied view cannot satisfy multi-view evidence.
6. Trace schema is complete, finite, continuous, strictly monotonic, and uses
   one common non-empty run identity.
7. Every non-initial trace row has finite positive `dt`, smoothing rates, and
   speed limits, and actual motion is within the recorded bound.
8. Side remains constant and valid. Side and overview poses remain external and
   geometrically distinct from the chase view.
9. Plan, root, and occupancy XYZ series are all mandatory, non-empty, finite,
   hashed, and have genuine Z provenance.
10. At least one valid SCAN trajectory ID exists and its time association is
    valid.
11. Material audit contains only eligible robot visual prims, opacity 1,
    emission 0, non-empty robot hashes, and independently measured equal
    before/after physical/sensor inventories.
12. Metadata hashes and exact fields match the actual files.
13. No output path existed before the current fresh packaging operation.
14. Automated presentation PASS cannot change a navigation FAIL into PASS and
    cannot satisfy AC55.

The validator itself must return a structured failure report rather than crash
on malformed JSON, NaN, missing fields, broken media, or absent tools.

## 11. Runtime Identity and Launcher Wiring

Wire the quality profile, three view configurations, output paths, and enabled
state through the smallest task-owned execution path, including:

- Office launcher argument construction;
- shared launcher only if actually required;
- `effective_input.txt`;
- `runtime_composition.json`;
- `run_identity.json`;
- `qualification_report.json`;
- final output/hash manifest.

The qualification report must add dashboard/video hashes after rendering, not
check for them before they exist and then omit them. Record source hashes for
the runner, presentation module, renderer, validator, launchers, and frozen
configs. Default-off runs must remain byte-for-byte compatible in their
argument behavior and must not create review outputs.

## 12. Required Tests

Add runner-level and real-CLI regression tests. Do not limit testing to helper
math.

Required positive tests:

- preserved chase-camera golden equations and composition;
- side and overview camera geometry;
- bounded deterministic smoothing for both external cameras;
- one root-state snapshot feeding three renders;
- no `env.step()` between renders;
- explicit camera pose set before every render;
- writer, trace, frame index, physics step, and simulator time alignment;
- actual before/after inventory collection through a testable adapter;
- eligible visible-mesh selection and collision/invisible exclusion;
- synthetic end-to-end real CLI rendering with three tiny H.264 videos and
  genuine non-empty plan/root/occupancy XYZ;
- 3D output and metadata change when real Z changes;
- default-off compatibility.

Required negative tests include:

- omitted ROS events, metrics, run identity, effective input, material audit,
  or acceptance/config identity;
- empty plan, empty metrics/root series, empty occupancy, and zero Z provenance;
- `dt=NaN`, non-positive `dt`, missing/empty run identity, side flip, camera
  overspeed, overview collapse onto another view, duplicate camera files;
- fabricated material audit targeting the Office floor, opacity below 1,
  non-zero emission, empty asset hash, empty inventory, copied post inventory,
  and altered physical/sensor inventory;
- wrong codec/profile/pixel format/resolution/fps/frame count;
- corrupted or truncated video where header frame count exceeds decoded frames;
- existing file, directory, symlink, or candidate38/39 output target;
- hard-coded dashboard PASS labels when evidence is absent or failing;
- hash mismatch and metadata mismatch;
- malformed B-spline/time association without fallback.

The five exact Codex Round 2 reproductions must now return failure:

```text
omitted_provenance_passed=False
nan_dt_missing_run_identity_passed=False
fabricated_material_audit_passed=False
empty_plan_metrics_passed=False
overwrite_allowed=False
```

## 13. Commands and Logs

Run the exact targeted suite:

```bash
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest \
    integration.lite3_sim_bridge.tests.test_trajectory_review \
    integration.lite3_sim_bridge.tests.test_office_review_presentation
```

Run the complete bridge suite:

```bash
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest discover \
    -s integration/lite3_sim_bridge/tests -p 'test_*.py'
```

Also run:

- `python3 -m py_compile` for every changed Python file;
- `bash -n` for every changed shell file;
- `git diff --check`;
- Trellis task JSONL validation;
- changed-path audit against Owned Paths;
- candidate38/39 hash and mtime preservation checks for every locally present
  report-listed artifact.

Save exact command output and exit codes to:

`.trellis/tasks/08-17-office-crowd-review-visual-r2/logs/antigravity-round3-tests.txt`

## 14. Allowed Paths

Only modify paths already owned by `implement.md`, plus this task's Round 3 log
and return. In particular, the expected implementation paths are:

- `integration/lite3_sim_bridge/lite3_sim_bridge/run_isaac_v12_fallback.py`
- `integration/lite3_sim_bridge/lite3_sim_bridge/office_review_presentation.py`
- `integration/lite3_sim_bridge/lite3_sim_bridge/trajectory_review.py` only for
  a genuinely reusable backward-compatible helper;
- matching tests under `integration/lite3_sim_bridge/tests/`;
- task-owned Office/shared launcher files only when needed for real argument
  and effective-input wiring;
- this Trellis task directory.

Do not modify unrelated literature, surveys, historical runs, older tasks,
candidate evidence, sibling repositories, or documentation outside this task.

## 15. Success and Failure Signals

`READY_FOR_CODEX_REVIEW` requires all of the following:

- all Round 2 fail-open reproductions now fail;
- all required positive and negative tests pass;
- output overwrite capability is removed;
- three-view capture is wired through runner, identity, effective input, report,
  and manifest;
- material audit measures actual pre/post state;
- no fake dashboard PASS text remains;
- changed paths remain within scope;
- candidate38/39 remain unchanged;
- no remote run or candidate was created.

Return `BLOCKED` if Isaac-only APIs cannot be verified locally. Implement and
test the pure adapters, state the exact unverified layer, and do not promote mock
evidence into a runtime claim.

## 16. Return Format

Write:

`.trellis/tasks/08-17-office-crowd-review-visual-r2/antigravity-round3-return.md`

Use exactly this structure:

```text
STATUS: READY_FOR_CODEX_REVIEW | BLOCKED

RESOLVED_CODEX_FINDINGS
- Each Round 2 P1 finding, code location, and regression test.

MULTIVIEW_CONTRACT
- Exact first/side/overview outputs, camera equations/configs, quality profile,
  same-step proof, and default-off behavior.

CHANGED_PATHS
- Every changed or added path and purpose.

TESTS
- Exact command, exit code, test count, and log path.

NEGATIVE_REPRODUCTIONS
- Exact result for omitted provenance, NaN dt, fabricated material audit,
  empty plan/metrics, overwrite attempt, corrupt video, duplicate view, and
  hard-coded PASS cases.

SCOPE_CHECK
- Candidate38/39 preservation, owned-path audit, no remote, no candidate40, no
  AC55 update, no commit/push/archive.

KNOWN_LIMITATIONS
- Exact Isaac-only or visual-runtime behavior not yet verified.

CODEX_REVIEW_NEEDED
- Concrete items Codex must independently inspect and rerun.
```

Stop immediately after writing the return. Do not run remote Isaac, do not
generate videos or a new candidate, and do not archive. Codex must independently
review the local diff before a separate, explicitly authorized visual-preflight
execution package is prepared.
