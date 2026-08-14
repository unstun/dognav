# SCAN Forest V5 Closed-Loop Candidate

Status: frozen automated gate PASS; human review pending.

This bundle responds to the V4 human change request with one deliberately
harder run: the V12 `model_149999` policy carries the current Lite3 Pro URDF,
MID-360-like LiDAR and D435i-like depth sensor over the pinned native
`forest_gen` terrain while the ROS 2 Foxy SCAN stack commands a 0.50 m/s maximum
forward velocity. A deterministic pine trunk intersects the direct segment
from start to the single final goal. No scripted detour waypoint is supplied.

The SCAN cloud is derived only from rendered XYZ and sensor pose. A local
minimum geometry filter removes terrain-like returns before transport. Terrain
height functions, prim identifiers, proxy bounds, and obstacle labels are not
planner inputs; those scene-truth records remain evaluation evidence only.

The local repository is the source of truth. The RTX 5070 Ti workspace is an
execution copy. A candidate needs two preserved identical-input dry runs, local
sync-back of logs/video/results, and Dr Sun's explicit video review. Automated
PASS does not establish human acceptance, real-robot safety, localization, or
sensor-fidelity validation.

## Result

Two identical-input dry runs (`forest_v5_candidate_dryrun02` and
`forest_v5_candidate_dryrun03`) passed before the threshold file was frozen.
The uninterrupted frozen run is `forest_v5_review_candidate01`. It reached the
goal with 0.059 m XY error, issued a 0.50 m/s forward command, measured a 0.523
m/s planar-speed 75th percentile, produced five SCAN trajectories, maintained
1.014 m minimum root-to-tree-centre distance, and recorded zero non-foot
contact, watchdog events, sequence gaps, protocol errors, and command
reconnects.

The first full run and the targeted transport diagnostic remain under
`runs/`. They show why V5 initially failed: a forest ray result occasionally
required about 275 ms to synchronize from GPU to CPU. The server previously
processed the oldest queued command first and disconnected on its timestamp.
The corrected receiver atomically validates a buffered command batch, observes
every sequence, and applies only the fresh latest command. The 250 ms watchdog
and source-age limit were not relaxed.

All 145 files under the remote `results/` and `logs/` trees were copied back.
The local and remote sorted-content aggregate is
`48b3275971a0171d1f79d44b3fb81bcc6482457bdba2d46d1faa7015fa938289`.
Five videos decode fully, five ROS bags pass SQLite integrity checks, five
depth arrays are finite `58 x 87` data, and all 50 JSON/JSONL files parse.
The frozen acceptance evaluator was rerun locally and produced a byte-identical
PASS report (`30e9e042e...`).

The directly reviewable raw candidate is
`runs/results/forest_v5_review_candidate01/closed_loop.mp4`. Human-review boxes
remain deliberately unchecked.

The wrapper defaults to the candidate dry-run threshold. Reproducing the
frozen review run therefore requires the explicit environment override
`SCAN_V5_ACCEPTANCE_CONFIG=$RUN_ROOT/acceptance_thresholds_v5.json`; the
executed file and its hash are recorded in `input_sha256.txt` and
`run_identity.json`.
