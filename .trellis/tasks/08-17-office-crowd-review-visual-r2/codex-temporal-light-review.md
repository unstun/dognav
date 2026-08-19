# Codex Temporal-Light Review — 2026-08-18

## Scope and boundary

- Stage: experiment + analysis.
- `candidate38` and `candidate39` remain immutable.
- `office_crowd_review_native_rviz_preflight13` is a supplemental 10-second
  visual preflight, not a new formal candidate and not a replacement AC54 run.
- AC55 remains pending Dr Sun's explicit visual decision.

## Repair under review

- Preserve the existing first-view camera equations and all accepted camera
  geometry, materials, and resolutions.
- Disable histogram auto exposure and use a fixed film ISO derived from the
  declared exposure.
- After each camera switch, render three unchanged-state RTX/DLAA frames and
  encode only the final settled frame.
- Reject presentation evidence shorter than the requested simulator duration.

## Verified evidence

- First, side, overview, and simulator-time RViz videos: 251 fully decoded
  frames, 25 fps, 10.04 s.
- Last camera-trace simulator timestamp: 10.03 s.
- Presentation validator: PASS, no issues.
- Isaac bridge qualification: PASS, no runtime error.
- Native RViz live audit: PASS; planned path, actual path, current pose, and
  `world -> TORSO` agree with same-run ROS evidence.
- Targeted transport/presentation tests: 20 passed.
- Repository suite excluding the known missing `dryrun11/closed_loop.mp4`
  fixture: 143 passed, 1 deselected, 9 subtests passed.

## Diagnostic light-stability comparison

After frame 100, beyond the preserved first-view content-fallback interval,
the robust 24-tile inter-frame luma-change p99 is 0.378 versus 1.395 in
`preflight08`; the maximum is 0.550 versus 1.589. The overview p99 is 0.293
versus 0.794. These measurements support reduced illumination flicker but do
not substitute for human visual review.

## Human gate

AC55 is not checked. Dr Sun must inspect the four entity videos and explicitly
accept or reject the remaining visible lighting behavior.
