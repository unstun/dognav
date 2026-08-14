# Human review: Lite3 V12 forest preview

Automated status: `PASS`.

Human status: **change requested by Dr Sun on 2026-08-14**.

Review decision: retain this run as the bounded open-loop baseline and produce
a faster planner-driven obstacle-avoidance revision. This does not reject the
automated V4 evidence; it rejects `preview02` as the final review candidate.

Primary artifact:

`runs/results/preview02/forest_lite3_v12.mp4`

Playback note: the 8.118 s MP4 is sampled from simulator policy steps, not
wall-clock time. Use it to judge appearance and physical motion; use
`runs/results/preview02/isaac/metrics.jsonl` for exact command-phase timing.

## Review checklist

- [ ] The file opens and visibly contains a moving Lite3, not a still scene or
  an upstream Spot robot.
- [ ] The robot remains visible enough to judge the zero, forward, yaw, and
  final-zero phases.
- [ ] The body and sensor-rig silhouette are acceptable for this engineering
  preview.
- [ ] The uneven forest terrain and bounded vegetation are acceptable as the
  next integration scene.
- [ ] The visible brown trunk and grey rock proxies are understood as the
  shared PhysX/LiDAR/depth validation geometry, not final rendering quality.
- [ ] The observed motion has no visually unacceptable fall, body-ground
  collapse, explosive joint motion, or obvious teleportation.

## Decision

- [ ] Accept `preview02` as the V4 human-reviewed forest locomotion preview.
- [ ] Request a clean-render variant with validation proxies hidden.
- [x] Request a camera, terrain, vegetation, or motion change before acceptance:
  faster motion plus real SCAN obstacle avoidance.

Acceptance here does not authorize training, SCAN-Planner forest closed-loop
execution, or real-robot actuation.
