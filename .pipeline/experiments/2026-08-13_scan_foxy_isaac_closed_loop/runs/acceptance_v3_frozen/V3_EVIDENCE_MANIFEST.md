# V3 Evidence Manifest

## Decision Status

- Automated frozen gate: **PASS, 71/71**.
- Post-sync local re-evaluation: **PASS, 71/71**.
- Human review: **PENDING**.
- Evidence label: project integrated; one fixed-course simulation validated by
  automated gate only.

## Direct Review

- Full video:
  `results/acceptance_v3_frozen/closed_loop.mp4`
- Sensor-rig close-ups:
  `review_frames/02s_sensor_rig_closeup.png`,
  `review_frames/10s_sensor_rig_closeup.png`, and
  `review_frames/15s_sensor_rig_closeup.png`
- D435i depth preview: `review_frames/d435i_depth_preview_8x.png`
- Human checklist: `../../HUMAN_REVIEW.md`

## Formal Identity

| Item | Identity |
|---|---|
| V12 checkpoint | `a9d31dce90e6e8c564d955e473d6d3502f893d7ef5a5c1efaf5bb50d6b3d5450` |
| Canonical rig URDF | `d0a1be09f018c0ab31df26f69ad8e700bd88ec06ae5b0f4dfbcc4fddf21cec80` |
| Isaac rig URDF | `803d552703bcc4f72ce15f38b95bc3f62e3e4ada0b42bf3ecf71b32b6590bb9d` |
| Frozen acceptance config | `b8f42d04b33532191e8ded21fe705aba33b7cd5c4f1311372e1afcb9561cd9ad` |
| Formal video | `db230a6e5460c8db09a95a1742f435169bf4e32fbdc4f980ba085afc3903d26d` |
| Float depth sample | `f7461c7c8ae3f32463368f73d137da6eafc34df9bef554a64a1828a07f399831` |
| Depth preview | `bb1d7e888dca0a3bbc67d8f8611bd739dc9c69976d55d0e9a18ce842bf45ea80` |

## Machine-Readable Evidence

- `results/acceptance_v3_frozen/acceptance_report.json`: remote formal
  evaluator output.
- `local_acceptance_recheck.json`: independent evaluation using local synced
  artifacts.
- `results/acceptance_v3_frozen/isaac/run_identity.json`: checkpoint, policy,
  URDF, sensor, frame, seed, watchdog, and video identity.
- `results/acceptance_v3_frozen/isaac/runtime_composition.json`: imported
  bodies, joints, masses, inertias, fixed joints, collisions, and sensor-frame
  readback.
- `results/acceptance_v3_frozen/isaac/metrics.jsonl`: policy, PhysX, command,
  contact, and pose causal trace.
- `results/acceptance_v3_frozen/isaac/sensor_metrics.jsonl`: MID-360-like
  per-frame evidence.
- `results/acceptance_v3_frozen/isaac/depth_metrics.jsonl`: D435i-like
  per-frame evidence.
- `results/acceptance_v3_frozen/ros_summary.json` and `ros_events.jsonl`: Foxy
  topic/planner/command observations.
- `results/acceptance_v3_frozen/rosbag/`: ROS-side recording.
- `local_results_sha256.txt` and `remote_results_sha256.txt`: 22 synced result
  hashes; files compare equal.
- `local_logs_sha256.txt` and `remote_logs_sha256_absolute.txt`: five matching
  formal log hashes.

## Claim Boundary

- Pose is simulator truth, not LIO.
- The MID-360-like sensor is a geometric multi-mesh ray caster, not Livox
  packet timing, noise, intensity, weather behavior, or hardware parity.
- The D435i-like depth camera uses provisional simulated intrinsics and is
  logged concurrently; it is not fused into SCAN in V3.
- One seed, one flat course, and one static obstacle do not establish general
  navigation robustness or real-robot safety.
