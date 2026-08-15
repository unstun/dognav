# V8 R2 Official Isaac Human — Closed-Loop Qualification

## Disposition

- Stage: experiment + analysis.
- Visual preflight: automated `PASS`, accepted by Dr Sun on 2026-08-15.
- No-contact preflight 04: `PASS`.
- Two frozen same-input full runs: both `PASS`.
- Frozen review candidate 01: automated `PASS` and local replay `PASS`.
- Final status: ready for Dr Sun's raw/overlay video review; AC44 remains open.

This is simulated evidence only. It does not validate real-person safety,
semantic perception, social navigation, real MID-360/D435i behavior, or real
Lite3 actuation.

## Frozen composition

- Robot: the repository's Lite3 Pro sensor-rig URDF, V12
  `model_149999`, and the existing 1.0 m/s command boundary.
- Planner: Foxy SCAN with the unchanged V7 dynamic planner/controller
  configurations and geometry-only point-cloud input.
- Visible character: NVIDIA Isaac Sim 5.1 `male_adult_police_04`, referenced
  from the official 5.1 asset URL and not vendored.
- Animation: official Biped `ControlRigAPI` retarget output, replayed from a
  deterministic 101-joint cache at 30 Hz: 60 idle frames and 90 walk frames.
- Physical/sensor actor: one hidden 1.70 m by 0.30 m capsule under a separate
  kinematic root. It alone owns collision and both ray-sensor targets.
- Visual/physical registration: common schedule time, XY, and heading, with
  separate shoe-sole and capsule-centre vertical datums.
- Overlay: SCAN planned path in green, Isaac actual path in yellow/blue, and
  official-human actual path in red with label `Official human actual`.

The official wrapper hashes frozen by acceptance are:

- visible USDA: `2925cf7fe1f47876e542f984f82b8edad9b3bec38b2c1bd5e363d3bf919bae9d`;
- hidden proxy USDA: `2654a66e04d84ddf38534f76bd7af9ec3652a9ec1d86a52c7b01bfbb5eb2ab02`;
- cache content: `76c19b57ebd03e01820e6b9db79bde8f2f3e436302744ef457278af8d17ef5b3`;
- cache file: `ac58a683fe9dd85ec3ad0266c7653b289dc1dd9b256d2abac0cc96ac7e45cfcb`.

The runtime log records `isaacsim.exp.base-5.1.0`; the GPU record is RTX 5070
Ti, driver 580.126.09, 16303 MiB. NVIDIA source assets remain subject to the
NVIDIA/Omniverse terms accepted on that runtime and are not relicensed here.

## Failure history and root cause

All failed evidence is preserved locally under `results/` and `logs/`.

1. `no_contact_preflight01` failed at about 4.03 s with 1190.82 N non-foot
   contact and negative person clearance. The first preset plan started from
   the first odometry callback before the occupancy map had processed a cloud;
   rendered-person workload changed thread timing and exposed this latent race.
2. The causal fix makes preset waypoint mode wait for the first processed
   occupancy update. Remote rebuild then passed 82 C++/ROS tests.
3. `no_contact_preflight02` proved the fix physically: three safety replans,
   zero collision, and +0.163 m clearance. It remained `FAIL` only because 30 s
   wall time advanced 23.5 s of rendered simulation, below the 25 s evidence
   floor.
4. `no_contact_preflight03` reached the goal with zero collision and +0.100 m
   clearance. It exposed two legacy measurement couplings: ROS wall-clock
   throughput was compared against simulated sensor time, and curved avoidance
   samples were excluded from the high-speed sample gate.
5. The frozen gate now independently requires 8--12 Hz simulated sensing,
   7.5--12 Hz ROS wall-clock throughput, synchronized/no-gap transport, a
   1.0 m/s common limit, at least 0.9 m/s forward peak, and at least 20 curved
   avoidance samples above 0.8 m/s whose measured-speed P75 is at least 0.7
   m/s. Collision and clearance thresholds were not loosened.
6. `no_contact_preflight04` passed every automated check and froze the official
   wrapper hashes above.

## Repeated and final results

| Run | Status | SCAN trajectories | Response latency | Minimum person clearance | Non-foot collision | Goal error | Measured speed P75 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `no_contact_preflight04` | PASS | 7 | 0.10 s | 0.125 m | 0 N | 0.088 m | 0.955 m/s |
| `dryrun01` | PASS | 5 | 0.10 s | 0.279 m | 0 N | 0.100 m | 0.877 m/s |
| `dryrun02` | PASS | 4 | 0.20 s | 0.261 m | 0 N | 0.129 m | 0.974 m/s |
| `review_candidate01` | PASS | 5 | 0.10 s | 0.139 m | 0 N | 0.108 m | 0.859 m/s |

Dry runs 01 and 02 have byte-identical `effective_input.txt` files with SHA-256
`ca96e3828f550f14d7afed530f460746c94de5071a3f02221dd6db2a249b401e`.
Their source/config hash lists contain identical hash values; the only textual
difference is the run-specific path printed beside `effective_input.txt`.

## Local evidence verification

- All seven remote result trees and log trees were copied to this directory.
- A recursive local/remote file-hash comparison passed before the local replay
  report was added.
- Local acceptance replay of the frozen review candidate returned `PASS`.
- Both final videos decode as H.264, 1280 x 720, 17 fps, 469 frames, 27.588 s.
- Raw video SHA-256:
  `29c149368142a83c9d4a8cc1e2bcb02bf28565d5078366b79ec76feb85d350b9`.
- Overlay SHA-256:
  `ea2800b32b898c5aca90ae693867b26b49d5058cb71ea8dcfe6d9e5f074d82f4`.

## Human review gate

AC44 is not satisfied by the automated reports. Dr Sun must watch the complete
raw and overlay videos and judge person recognizability, gait, sensor-causal
avoidance, planned-versus-actual motion, terrain appearance, speed, clearance,
and terminal behavior. Until explicit acceptance, this task remains under
human review and the result must not be described as fully validated.
