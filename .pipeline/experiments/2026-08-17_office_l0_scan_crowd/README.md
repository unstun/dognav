# Office L0 Lite3 SCAN Crowd Trial

Status: automated AC51--AC54 passed in same-input candidates 38 and 39;
human visual review AC55 remains pending.

Change control for all new work is defined by `CHANGE_CONTROL.md`. The current
working revision, component versions, immutable run outcomes, evidence hashes,
and next authorized action are recorded in `revision_ledger.json`. Run
`validate_revision_ledger.py` before any new remote execution. The ledger does
not promote candidate38/39, mark AC55, or turn a visual preflight into formal
evidence.

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
