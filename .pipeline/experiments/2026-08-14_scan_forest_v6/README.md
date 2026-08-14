# SCAN Forest V6 1.0 m/s Review Candidate

Status: frozen automated gate PASS; human review pending.

V6 responds to Dr Sun's review of V5 with three bounded changes: a 1.0 m/s
clear-path ceiling across SCAN, the controller, the Foxy bridge, and the Isaac
receiver; a runtime-bounds correction for rock seating with simplified proxies
hidden from the final viewport; and a traceable review overlay showing the
sampled SCAN B-spline beside the accumulated Isaac PhysX root path.

The unchanged dependencies are V12 `model_149999`, its 450-value observation
and 12-action contract, the current Lite3 Pro sensor-rig URDFs, MID-360-like and
D435i-like simulation, `forest_gen`/STRIPE-kit commits, forest seed 14, the
start/goal, and the SCAN algorithm. No training or real-robot actuation is part
of V6.

## V5 diagnosis that V6 must close

V5 placed each source rock's centre-origin USD at the terrain height and also
rendered a fixed grey collision/sensor cuboid. The converted Rock 1 local z
bound is approximately `[-0.556, 0.549] m`; placing its origin on the terrain
therefore buries roughly half the source visual. Its local XY extent is also
about `1.535 x 1.263 m`, while the visible V5 proxy was fixed at
`0.72 x 0.72 m`. The apparent interpenetration is consequently a real geometry
composition defect, not just a camera artefact.

The first V6 correction sampled the full axis-aligned box and prevented
penetration, but human frame inspection caught a new defect: an empty high-side
box corner lifted the irregular source mesh above the sloped ground. That
preflight is preserved. The accepted implementation reads the converted USD's
actual mesh vertices, takes the lowest 20 mm surface band, and seats at least
one real support vertex 15 mm above terrain. It records the selected support
vertices, contact point, pre/post transform, source world bounds, and paired
proxy bounds. The registered proxy remains collision-enabled and targeted by
both sensors but is hidden in the review render.

## Review-video boundary

`closed_loop.mp4` remains the untouched simulator recording. The derived
`closed_loop_review_overlay.mp4` is generated only from hashed raw inputs:
complete `/planning/bspline` messages, Isaac `metrics.jsonl`, the run identity,
and the raw MP4. Its metadata records input/output hashes, timing association,
trajectory IDs, colours, and plot bounds. Automated decoding or acceptance is
not human approval.

## Result

The 1.0 m/s implementation passed two same-input dry runs before the numerical
gate was frozen. Their input hash sequences, effective inputs, upstream git
state, and terrain geometry hash match. The first frozen run,
`forest_v6_review_candidate01`, passed all 100 checks but retained an obsolete
human-readable geometry-method string in its run identity. It is preserved
unchanged and superseded rather than overwritten. The metadata-corrected rerun,
`forest_v6_review_candidate02`, also passed all 100 automated checks. It
reached the goal with 0.039 m XY error, issued a 1.000 m/s forward command,
measured a 0.966 m/s planar-speed 75th percentile and a 0.967 m/s low-yaw/high-
command 75th percentile, maintained 0.831 m centre clearance from the direct-
path pine, produced a 0.836 m planned detour, and recorded zero non-foot
contact, watchdog events, sequence gaps, protocol errors, or reconnects.

The endpoint controller now latches zero after it first reaches the final
trajectory point inside the 0.15 m finish tolerance. This closes the preserved
`forest_v6_candidate_dryrun01` failure, where the robot reached the goal but
the controller repeatedly corrected small post-goal drift at about 0.12 m/s.

The final raw and overlay videos are regular 1280 x 720 H.264 files with 495
frames and 29.117647 s encoded duration. The overlay contains two complete
SCAN B-splines, uses the recorded PhysX root path, and has a maximum plan-to-
pose timestamp association error of 15.970922 ms. All 217 files produced by
the seven remote V6 run directories match their local copies; the sorted remote
manifest aggregate is
`c10ecad5190a3b52c1c4d4e7958975f008f27d2c1d82e42ea64bc64e67d92b94`.

The directly reviewable files are:

- `runs/results/forest_v6_review_candidate02/closed_loop_review_overlay.mp4`
- `runs/results/forest_v6_review_candidate02/closed_loop.mp4`

Automated PASS and agent frame inspection do not establish Dr Sun's human
acceptance, calibrated sensor parity, localization performance, multi-scene
robustness, or real-robot safety.
