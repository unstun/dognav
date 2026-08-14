# SCAN Forest V7 Dynamic-Obstacle Review Candidate

Status: R2 frozen automated gate passed; Dr Sun human review is pending.

V7 preserves the V6 Lite3 sensor-rig URDF, `model_149999` V12 weights,
forest seed/start/goal, 1.0 m/s limit, transport, and SCAN planner. One orange
collidable cylinder waits at `[-2.7, 2.0]` until the first accepted nonzero
body command, moves at 0.8 m/s to the nominal route, holds there for 2.5 s,
then continues to `[-2.7, 4.8]`. This command-relative schedule removes the
simulator-start race found in dry run 11.

The same transform-tracked prim is rendered by the MID-360-like ray caster and
D435i-like depth camera. SCAN receives only rendered point geometry. Obstacle
truth is limited to motion/readback, hit classification, synchronized
clearance, and the review overlay; it never creates a point, trajectory, or
robot command.

Trellis review superseded candidate 01 because its collision-replan deferral
reused a broader execution-frozen signal. R2 separates a catch-up-only signal
and qualifies a 0.20 m/s minimum command only inside bounded catch-up. Dry runs
16 and 17 then passed 120/120 with identical source/config inputs; dry run 16
exercised a 0.719 m catch-up while dry run 17 exercised normal tracking.

Candidate 02 passed the frozen R2 gate, but final cross-scenario review found
that the shared runner did not initialize V7-only hold variables for non-V7
callers. The compatibility-only initialization changed the recorded runner
hash, so candidate 02 is preserved and superseded. The post-fix R2 candidate
`forest_v7_review_candidate03` passed 120/120 without threshold changes. Key
candidate measurements are:

- 0.739 m minimum synchronized dynamic-obstacle surface clearance;
- 0.901 m minimum centre clearance from the declared static tree;
- 0 N maximum non-foot contact, with no termination or base teleport;
- 0.954 m/s overall measured planar-speed P75 and 1.006 m/s P75 under high
  forward commands;
- three successful SCAN B-splines and a 2.50 s detection-to-plan response;
- a continuous two-second stopped window at the goal, 0.089 m final goal
  error, and 0.039 m maximum drift after that stopped window.

The raw and trajectory-overlay MP4s, ROS bag, metrics, sensor records, run
identity, acceptance reports, and remote hash manifests are under
`results/forest_v7_review_candidate03/`. R2 dry runs 16 and 17 are also copied
back in full. Candidate 01, earlier passing dry runs, failure logs, and key
reports are retained under `logs/` and `results/`; candidates 01 and 02 and no
failed run were overwritten or relabeled as the review candidate.

This is a single-seed reactive moving-occupancy simulation result. It is not
predictive dynamic planning, sensor hardware parity, station-keeping
validation, or real-robot validation. Automated PASS does not satisfy the
human-review gate.
