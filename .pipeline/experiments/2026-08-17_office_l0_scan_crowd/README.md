# Office L0 Lite3 SCAN Crowd Trial

Status: automated AC51--AC54 passed in same-input candidates 38 and 39;
human visual review AC55 remains pending.

Change control for all new work is defined by `CHANGE_CONTROL.md`. The current
working revision, component versions, immutable run outcomes, evidence hashes,
and next authorized action are recorded in `revision_ledger.json`. Run
`validate_revision_ledger.py` before any new remote execution. The ledger does
not promote candidate38/39, mark AC55, or turn a visual preflight into formal
evidence.

The active build is `office-v2.0.1-go2-geometry-preflight` with profile
`upstream_go2_reference`. One MID-360 scan is represented atomically as
ground-inclusive `/quad_0/cloud_raw` for native RViz and geometry-filtered
`/quad_0/cloud` for SCAN. The profile borrows exactly five collision-envelope
values from the pinned upstream Go2 configuration while keeping Lite3 speed at
0.50 m/s and preserving the Office map, sensor, policy, controller, crowd, and
acceptance contracts. Flat 10.04 s run `office_v2_0_1_go2_geometry_preflight02`
has 101/101 same-scan audits and directly openable master/transfer videos. The
first run and two postprocessing failures remain preserved. Full-duration
`dryrun01` is an immutable packaging failure; `dryrun02` passed the declared
60-second flat terminal, crowd, dual-cloud, RViz and delivery gates with
601/601 paired scans. Its separate directly playable review copy is 9,176,726
bytes. No non-flat run, fresh AC54, AC55, formal candidate, training, or
real-robot execution was performed.

This experiment evaluates whether the official Isaac Sim 5.1 Office L0 scene
can support the pinned Lite3 V12/SCAN closed loop with eight official animated
pedestrians. The local repository is the source of truth. The RTX 5070 Ti
workspace under
`/home/sun/machine-dog-nav-runs/2026-08-17_office_l0_scan_crowd` is an execution
copy only.

The work must pass, in order: source-mesh collision coverage, static articulated
Lite3 support/contact, sensor visibility, eight-person swept-route prechecks,
and two same-input closed loops. Visual scene loading alone cannot satisfy any
of those gates.
