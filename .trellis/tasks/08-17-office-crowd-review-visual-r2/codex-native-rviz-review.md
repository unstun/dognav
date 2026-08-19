# Codex native RViz supplemental review

Date: 2026-08-18

Stage: experiment + analysis

## Outcome

`office_crowd_review_native_rviz_preflight01` passed the automated presentation
and native-topic evidence checks. It is supplemental visual evidence only. It
does not replace candidate38/39, does not alter AC54, and does not satisfy AC55.

## Verified facts

- The first-person, high-oblique side, and overview streams are direct H.264
  High, 1920x1080, 25 fps videos with 251 frames and 10.04 s duration.
- The high-oblique camera uses the reviewed 8 m height configuration.
- `plan_manage/launch/default.rviz` ran on display `:0` of `gpu5070ti` inside
  the same Foxy container as SCAN-Planner.
- The captured RViz stream is H.264 High, 1920x1080, 25 fps, with 2,867 frames
  and 114.68 s wall-clock duration.
- Native capture contains 50 frames. `/quad_0/cloud`,
  `/grid_map/occupancy`, and `/grid_map/occupancy_inflate` are nonempty, with
  zero decode errors.
- Contact-sheet inspection shows the native SCAN layers, sliding-map boundary,
  trajectory, and changing occupancy; the recording is not an empty RViz grid.
- The Office presentation report is `passed: true` with an empty issue list.
- Remote and local pulled artifacts match by checksum dry-run.
- The frozen candidate38/39 hashes still match the reviewed report.

## Visual boundary

- The pure-white Lite3 has low contrast against white Office tiles. This is the
  direct consequence of preserving the requested white robot appearance.
- The first-person stream is sharp, but nearby Office geometry can temporarily
  occlude the chase camera.
- The native SCAN view uses the upstream RViz colors. In particular, inflated
  occupancy is magenta; this is not robot recoloring or a synthetic dashboard.
- The RViz recording is wall-clock long because the simulator runs slower than
  real time. The full recording is retained instead of hiding startup or
  replanning intervals through aggressive trimming.

## Preserved negative attempts

- `office_crowd_review_preflight36`: rejected a decimal duration before a
  result directory was created.
- `office_crowd_review_preflight37`: Office run passed, but a separate RViz
  container did not receive occupancy; the fail-closed recorder emitted no
  empty RViz video.

## Pending human decision

Dr Sun must inspect the entity videos and explicitly decide AC55. No automated
test or this review can mark AC55 complete.

## Clarification and final submitted preflight

Dr Sun clarified that the original offset chase camera is the intended first
view. The issue was its inconsistent image quality, material, and lighting, not
its camera geometry. The D435i optical-frame streams in preflight02/03 therefore
remain preserved intermediate attempts and are not submitted for AC55.

`office_crowd_review_native_rviz_preflight06` is the current human-review
preflight:

- The first view restores the exact candidate38/39 chase equations. The 8 m
  high-oblique external third view and the overview composition remain intact.
- All three raw camera streams are H.264 High, YUV420p, BT.709, 2560x1440,
  25 fps, 251 frames, and 10.04 s. They fully decode locally.
- Every visible Lite3 mesh uses the same pure-white, opaque, non-emissive review
  material. The material audit remains confined to visual mesh prims.
- All three camera renders use the same render-only Office cutaway and restore
  the scene before physics/sensing/planning continues.
- The 5070 Ti native RViz source has 4,103 frames. The submitted simulator-time
  RViz entity has 251 frames mapped one-for-one to the camera trace, with a
  maximum capture quantization error of 0.019916 s. It selects only frames from
  the source capture; it does not synthesize or replay SCAN data.
- Remote and local hashes match for all eight delivered MP4 files. The Office
  presentation validator and Isaac qualification report both pass.
- Preflight04 and preflight05 are retained negative synchronization attempts:
  the former exposed a backward wall-clock jump, and the latter exposed a
  partial concurrently-read JSONL row. Preflight06 uses a monotonic clock and
  accepts only complete newline-terminated rows.

AC55 remains unchecked and exclusively owned by Dr Sun.

## Planned/actual/current/URDF revision

`office_crowd_review_native_rviz_preflight08` supersedes preflight06 only as
the current supplemental visual preflight; it does not replace candidate38/39.
The camera geometry and presentation remain unchanged. Native Foxy RViz now
shows:

- the orange path sampled from live `/planning/bspline` messages;
- the green accumulated path from measured `/quad_0/body_pose` messages;
- a yellow current-pose arrow plus the TORSO axes;
- the canonical Lite3 URDF driven by same-run measured joint states.

The live audit is PASS with 70 body/current/root-transform publications and two
160-point SCAN trajectories. The rosbag contains 70 joint-state messages and
the matching review topics. All four submitted videos have 251 frames and
10.04 s duration, fully decode locally, and match the remote hashes. The three
camera videos are 2560x1440; the synchronized native RViz video is 1920x1080.

Preflight07 is retained. Evidence review showed that its startup missing-frame
messages preceded the first measured joint state and did not prevent the full
RobotModel from rendering, but preflight08 adds a more legible current-position
arrow and thicker plan/actual lines.

This remains a short visual preflight. AC55 is still unchecked and Dr Sun must
make the decision after watching the entity videos.
