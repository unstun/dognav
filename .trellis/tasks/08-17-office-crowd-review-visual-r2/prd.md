# Revise Office Crowd Human-Review Visualization

## Goal

Create a new, independently reviewable Office L0 crowd candidate that makes the
Lite3 easy to distinguish, preserves the existing delivered video viewpoint as
Dr Sun's requested first view, adds a genuinely external side-observer
third-person view, and shows the SCAN planned path and physical Lite3 path
truthfully in three dimensions. The result should let Dr Sun judge motion,
avoidance, and path tracking without weakening or relabeling the existing
automated evidence.

## Background

- Office crowd candidates 38 and 39 passed AC54 but remain pending the
  human-owned AC55 gate.
- Dr Sun reported that the Lite3 looks dim or grey compared with earlier
  evidence and is difficult to distinguish from the scene.
- Dr Sun clarified that "first-person" means the viewpoint already used by the
  delivered candidate38/39 video. It must not be replaced by a literal
  dog-mounted or D435i optical-frame camera.
- Dr Sun later selected one uniform white Lite3 appearance. Visual separation
  must come from consistent high-quality rendering, lighting, and shadows, not
  from assigning unrelated colors to individual robot parts.
- Dr Sun requested one additional genuine third-person camera placed reasonably
  beside the robot/scene, plus a three-dimensional presentation of planned
  versus actual trajectories.
- After reviewing preflight06, Dr Sun found the camera views basically
  satisfactory but required native RViz to show the SCAN planned path, measured
  Lite3 path, current robot pose, and the pinned Lite3 URDF model together.
- After reviewing the later 60-second native-RViz presentation, Dr Sun found
  that many official pedestrians played a walk clip while their root pose was
  stationary. Dr Sun approved a new corrective iteration. The prior run is
  preserved as rejected visual evidence; its AC54 result is not reused.
- Dr Sun simplified the user-facing delivery to two synchronized panels only:
  the high external third-person view and native 5070 Ti RViz. Compatibility
  streams may remain as internal evidence but are not submitted as review
  views.
- The requested revision is an AC55 visual change request. Candidates 38 and 39
  remain immutable evidence and AC55 remains unchecked.
- On 2026-08-19 Dr Sun separately approved replacing the Office run's uniform
  16-channel, 12 m approximation with a source-backed MID-360 simulation. This
  is a new sensor-input revision, not a presentation-only change, so every new
  preflight and candidate must rerun the automated navigation/safety gates.
- Existing automated results cannot be promoted, rejected, or rewritten by a
  presentation-only change.
- Candidate39 and the earlier forest review candidate use the same Isaac-safe
  Lite3 asset SHA-256 (`803d552703bcc4f72ce15f38b95bc3f62e3e4ada0b42bf3ecf71b32b6590bb9d`).
  The robot asset did not change between those presentations.
- The current Office runtime adds a `900.0`-intensity dome light, while the
  imported URDF leaves the main torso, hip, and thigh visuals without explicit
  material colours. Together with the white Office floor, this is the supported
  explanation to test for the weak robot/background contrast; it is a
  presentation defect, not evidence of a physics change.
- The current runtime records only one high, root-relative, offset chase-camera
  stream. That stream is the first view to preserve under Dr Sun's terminology.
  Its review renderer samples three-coordinate SCAN B-splines but projects only
  XY into a top-down inset. Candidate39 nevertheless contains genuine height data:
  recorded B-spline control-point Z spans about `0.295--0.854 m`, and physical
  root Z spans about `0.282--0.350 m`.
- This Codex session uses an inline Trellis harness. Codex implements and checks
  the bounded revision directly; the AC55 decision remains human-only.

## Requirements

### R1 — Immutable evidence boundary

Do not edit, replace, rename, or delete candidate38 or candidate39 artifacts.
Create a new candidate directory and preserve its own configuration, logs,
videos, machine-readable metrics, and hashes.

### R2 — Lite3 visual legibility

The new review video must make the complete articulated Lite3 visually
distinguishable from the Office floor and nearby dark furniture. Any material,
lighting, exposure, or annotation change must be presentation-scoped and must
not change collision, mass, policy, sensor, planner, pedestrian, route, or
acceptance behavior. The review material is uniform opaque, non-emissive white
across the visible Lite3 meshes.

### R3 — Preserve the existing first view

Keep the current candidate38/39 root-relative chase-camera composition and
behavior as the primary video view. This is the user-facing first view for this
task. Do not substitute a head-mounted, D435i, cockpit, or robot-eye viewpoint.

### R4 — Genuine external third-person view

Record a synchronized external side-observer view from a camera visibly separate
from the robot's current chase view. It must keep the complete Lite3, nearby
official pedestrians, and route context visible well enough to judge
interaction, clearance, gait, and terminal behavior. The camera must follow
smoothly from the robot's side rather than remain fixed, mount to the robot, or
teleport between viewpoints. Lateral distance, height, trailing offset, and
smoothing parameters may be tuned only in the short visual preflight and must
then be frozen in the effective input for full runs.

### R5 — Truthful 3D trajectory presentation

Show the active SCAN planned trajectory and accumulated physical Lite3 root
trajectory in a three-dimensional, metrically consistent representation.
Every displayed point must be derived from recorded run data with explicit
frame, axis, unit, timestamp, and provenance. Do not lift a two-dimensional
line into 3D by hand, interpolate a decorative route, or use pedestrian ground
truth as planner input.

### R6 — Dynamic-event context

The review presentation must retain enough detected dynamic occupancy and
replanning context for Dr Sun to relate pedestrian motion to a causally later
SCAN path change.

### R7 — Execution and independent verification

After Dr Sun approves the revision, Codex performs the bounded inline
implementation, checks scope and evidence identities, reruns the declared
validation, and inspects the final media before submitting it to Dr Sun. Codex
may not mark AC55 complete.

### R8 — Complete native RViz state

The 5070 Ti native Foxy RViz view must subscribe to live same-run sources and
visibly distinguish the sampled `/planning/bspline` path from the accumulated
`/quad_0/body_pose` path. The current pose must drive `world -> TORSO`, and the
pinned Lite3 URDF RobotModel must use measured Isaac joint positions. A GO2
model, synthetic gait, video overlay, or post-run drawn path is not acceptable.

### R9 — Pedestrian root-motion fidelity

An official pedestrian may use the walk clip only while its registered visual,
physical capsule, and sensor representation translate together. The corrective
candidate keeps the two route-crossing events single-pass and repeats only the
six background routes over their frozen endpoints. Repeating pedestrians idle
during a bounded smooth 180-degree turnaround. The runtime records velocity,
phase, direction, cycle, and animation clip per person, and fails automatically
if walk-in-place or idle sliding exceeds the declared tolerance.

### R10 — Two-panel review delivery

The directly submitted composite contains only the synchronized high external
third-person panel and native 5070 Ti RViz panel at full 1920 x 1080 per panel.
Raw compatibility views remain run-owned evidence and must not be confused with
the requested deliverable.

### R11 — Source-backed MID-360 geometric input

The new Office preflight uses the exact ordered `mid360.csv` from the pinned
MIT-licensed Livox simulator, a 0.1 m blind-zone filter, a conservative 40 m
ray-cast range, 10 Hz scans, and 20,000 ordered rays per scan. The cloud frame,
sensor pose, body pose, and frame timestamp must come from the same Isaac
physics step. Run identity must state that reflectivity/intensity, multiple
returns, weather, electronic noise, and intra-scan motion distortion remain
unmodeled. The legacy uniform mode stays available only for reproducibility of
older inputs and is not relabeled as MID-360.

## Acceptance Criteria

- [ ] **AC1 — Preservation:** candidate38 and candidate39 hashes remain
  unchanged, and the new result uses a distinct candidate directory.
- [ ] **AC2 — Legibility:** the full Lite3 body is consistently distinguishable
  from the floor and nearby furniture in both requested review perspectives.
- [ ] **AC3 — Synchronized perspectives:** the preserved current view and the
  external side-observer view cover the same uninterrupted run with verifiable
  frame/time alignment.
- [ ] **AC4 — Smooth external observation:** the new camera remains visibly
  external and predominantly lateral to the robot, keeps the complete robot and
  nearby interaction context readable, and has no unlogged jump, side flip, or
  second-run substitution.
- [ ] **AC5 — Physical fidelity:** both views show the same articulated physical
  motion, official pedestrians, collisions or clearances, and terminal state;
  no teleport, replay mismatch, or hidden rerun is presented as one run.
- [ ] **AC6 — 3D provenance:** planned and physical trajectories are rendered
  from recorded SCAN and simulator pose samples in declared coordinates and
  units, with hashes or equivalent identity linkage to the new run.
- [ ] **AC7 — Causal readability:** the presentation allows a reviewer to see
  the relevant pedestrian/dynamic occupancy context and the subsequent local
  plan change without relying on an unverified caption.
- [ ] **AC8 — Automated integrity:** the new run satisfies the existing Office
  crowd automated safety, goal, protocol, watchdog, causal-replanning, and
  evidence-sync gates; presentation changes do not silently relax thresholds.
- [ ] **AC9 — Independent Codex verification:** Codex reviews the complete local
  diff and new evidence, verifies the declared checks, and records any failure
  without hiding failed preflights.
- [ ] **AC10 — Native RViz completeness:** the native synchronized RViz entity
  visibly contains distinct planned and actual paths, current `TORSO` pose, and
  the pinned Lite3 URDF driven by same-run measured joint states.
- [ ] **AC11 — Human decision:** Dr Sun watches the submitted review material and
  explicitly accepts or rejects the new candidate. Automated checks, Gemini,
  and Codex cannot satisfy this criterion.
- [ ] **AC12 — Pedestrian motion fidelity:** all eight official pedestrians use
  the walk clip only with non-zero root motion, idle during endpoint turns, and
  maintain real crowd translation throughout the review interval.
- [ ] **AC13 — Two-panel delivery:** the review composite contains only the high
  external third-person view and synchronized native RViz, each at 1920 x 1080.
- [x] **AC14 — MID-360 source and timing:** the fresh run pins the Livox pattern
  SHA-256 and commit, emits 20,000 ordered rays per 0.1 s scan over the declared
  angular envelope, uses the 0.1--40 m geometric range, and records same-step
  body/sensor pose plus frame timestamp without reusing old AC54 evidence.

## Out of Scope

- Editing or relabeling candidate38 or candidate39.
- Replacing the Lite3 policy, SCAN algorithm, Office route endpoints, or frozen
  automated thresholds merely to improve the video. The user-approved opt-in
  background ping-pong traversal is limited to the six existing background
  endpoints and is a new scenario input with fresh automated gates.
- Real-robot actuation, training, predictive pedestrian modeling, social
  navigation, or a broader multi-scene validation claim.
- Decorative 3D curves or truth-based planner steering.

## Key Product Decisions

- Preserve `closed_loop.mp4` as the existing user-requested first view, add a
  separate full-resolution external side-observer video, and generate one
  synchronized dashboard video for side-by-side evidence review.
- Submit only the external high third-person and native RViz panels in the final
  review composite; keep the other raw streams as internal compatibility
  evidence.
- Make background pedestrian root motion continuous by repeating their frozen
  segments in both directions with a 0.6-second idle turnaround. Keep the two
  route-crossing pedestrians single-pass so they do not return into Lite3 after
  the causal crossing. Treat this as fresh scenario input and rerun automated
  acceptance rather than inheriting AC54.
- Use a smoothly side-following external observer. Keep one configured side
  during normal capture, apply simulator-time-based smoothing and motion bounds,
  and log both desired and realized camera poses. Do not silently orbit, flip
  sides, or cut to another run.
- Keep the pinned robot URDF, meshes, physics, and sensor extrinsics unchanged.
  Improve legibility with a documented, Office-only review material override.
  The separately approved MID-360 ray-pattern/range revision is opt-in, pinned,
  and requires fresh automated evidence; it does not alter the URDF mount.
- Use a local, equal-scale 3D evidence panel driven only by recorded SCAN,
  simulator-root, and captured occupancy samples. Do not exaggerate the Z axis.
- Require a short visual preflight before any new full closed-loop candidate.
  The expected next formal name is candidate40, but the runner must re-check the
  local and remote namespaces and select a fresh name instead of overwriting.
