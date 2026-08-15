# V8 Verification Record

## Frozen identity

- Review run: `v8_human_review_candidate01`
- Frozen acceptance SHA-256:
  `14265b9e2d331506708186fdd4fa37ba069ce99b189fe818a78e2e95687ae48a`
- Effective-input SHA-256 shared by both passing dry runs and the candidate:
  `b0330f7375a0dd26c307180b475d293d6ea5528d0d957887b561d718f3118bfe`
- Generated human USDA SHA-256:
  `24efd3335c5a5d2654ff7eaf14c93052f50045d62d7342de7cac3ff10bd183a0`
- V12 checkpoint SHA-256:
  `a9d31dce90e6e8c564d955e473d6d3502f893d7ef5a5c1efaf5bb50d6b3d5450`
- Canonical / Isaac-safe sensor-rig URDF SHA-256:
  `d0a1be09f018c0ab31df26f69ad8e700bd88ec06ae5b0f4dfbcc4fddf21cec80` /
  `803d552703bcc4f72ce15f38b95bc3f62e3e4ada0b42bf3ecf71b32b6590bb9d`

## Qualification sequence

The corrected seven-part high-visibility geometry passed a 10 s no-contact
preflight and two 45 s same-input candidate runs. Thresholds and the generated
asset hash were then frozen before the uninterrupted review candidate.

| Run | Gate | Human clearance | Contact | Planner detour | Goal error |
|---|---:|---:|---:|---:|---:|
| `v8_human_candidate_dryrun02` | 125/125 | 0.352 m | 0 N | 1.011 m | 0.024 m |
| `v8_human_candidate_dryrun03` | 125/125 | 0.297 m | 0 N | 0.848 m | 0.058 m |
| `v8_human_review_candidate01` | 125/125 | 0.319 m | 0 N | 1.025 m | 0.019 m |

The review candidate recorded 25 LiDAR and 22 depth detections while the limbs
were swinging. Maximum gait swing was 0.4363 rad with zero opposition and
neutral-pose error. SCAN produced three successful trajectories; measured speed
P75 was 0.844 m/s overall and 1.008 m/s during high-command samples.

## Local evidence checks

- Raw video, overlay, acceptance report, and run identity matched remote
  SHA-256 exactly.
- Raw and overlay MP4s decode as H.264, 1280x720, 609 frames, 35.82 s.
- ROS bag SQLite integrity returned `ok` with 4781 messages.
- Every copied JSON and JSONL record parsed successfully.
- Local acceptance re-evaluation passed 125/125.
- Local and remote bridge suites each passed 71/71.

Final Trellis review tightened the local V8 stage check so both LiDAR and depth
transform-tracking booleans are required, rather than merely displayed in the
report. The preserved candidate records both as true and still passes 125/125
under the stricter verifier; simulator behavior and frozen thresholds were not
changed or rerun for this evidence-only check.

## Preserved failure boundary

`v8_human_stage_preflight01` failed because the audit compared the
`{ENV_REGEX_NS}` template with Isaac's expanded runtime regex. Preflight 02
proved geometry, gait, and both sensor paths but was intentionally too short for
the navigation gate. `v8_human_candidate_dryrun01` reached the goal but collided
with the first narrow visible body: 2319.98 N maximum non-foot contact and
-0.139 m synchronized clearance. It remains a failed run. The owning fix made
the visible torso/pelvis commensurate with the unchanged 0.30 m physical
capsule; no route, actor timing, policy, speed limit, or collision threshold was
relaxed.

## Claim boundary

This is one single-seed Isaac Lab forest candidate with reactive SCAN geometry
replanning, a geometric human proxy, pinned V12 weights, and the pinned Lite3
sensor-rig URDF. It does not establish semantic person detection, social or
predictive navigation, human behavior simulation, hardware sensor fidelity,
LIO behavior, real-person safety, real-robot safety, or human acceptance.
