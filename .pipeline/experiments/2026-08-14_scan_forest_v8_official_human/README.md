# V8 R2 Official Isaac Human

This directory contains the V8 R2 official-human visual preflight, failed and
passing no-contact preflights, two identical-input full SCAN runs, and one
frozen review candidate.

The visible actor references NVIDIA Isaac Sim 5.1
`male_adult_police_04`; NVIDIA character, texture, skeleton, and source
animation content is not copied into this repository. The generated local
USDA files only reference that versioned content. A separately generated
101-joint retarget cache is retained as experiment evidence. Use and
redistribution remain subject to the NVIDIA/Omniverse terms accepted by the
execution environment; this repository does not relicense NVIDIA assets.

The final automated disposition is `PASS` for AC40--AC43. AC44 remains an
explicit human-only gate: Dr Sun must watch both complete candidate videos and
accept or reject the result.

Direct review files:

- raw simulator video:
  `results/v8_official_scan_review_candidate01/closed_loop.mp4`;
- SCAN planned path, Isaac actual path, and official-human actual path overlay:
  `results/v8_official_scan_review_candidate01/closed_loop_review_overlay.mp4`;
- automated acceptance:
  `results/v8_official_scan_review_candidate01/acceptance_report.json`;
- local deterministic replay:
  `results/v8_official_scan_review_candidate01/acceptance_report.local_replay.json`.

See `REPORT.md` for the exact failure history, input-parity statement, physical
metrics, hashes, and remaining claim boundary.
