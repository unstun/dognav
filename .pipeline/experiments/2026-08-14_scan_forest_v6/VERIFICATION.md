# V6 Verification Record

Status: frozen automated checks passed; Dr Sun's video review is pending.

## Preserved diagnosis and qualification order

- `v5_geometry_diagnosis_contact_sheet.png` reproduces the visible V5
  rock/proxy defect. Runtime bounds show the large source rock is about
  1.535 x 1.263 x 1.105 m while the visible V5 proxy was a fixed
  0.72 x 0.72 x 0.46 m cuboid.
- `forest_v6_geometry_preflight01` proved that full-AABB conservative seating
  removed terrain intersection, but human frame inspection rejected the
  resulting floating rock. That machine-pass/human-fail distinction is
  preserved.
- `forest_v6_geometry_preflight02` used the real lowest 20 mm mesh-vertex band.
  All three rock contact supports recorded 0.015 m terrain clearance and the
  hidden proxy/source bounds agreed within 0.000001 m.
- `forest_v6_candidate_dryrun01` reached the goal and avoided the tree, but
  failed the frozen-candidate prerequisites because 30 s wall time produced
  only 24.2 s of physics/video and the controller hunted around the endpoint.
  No threshold was relaxed; the controller gained a tested terminal-stop
  latch and the subsequent same-input duration was fixed at 36 s.
- `forest_v6_candidate_dryrun02` and `forest_v6_candidate_dryrun03` both passed
  100/100 candidate checks with identical input digest sequences, effective
  input, upstream git state, and terrain hash. Only then was
  `acceptance_thresholds_v6.json` frozen without changing any numerical value.
- `forest_v6_review_candidate01` passed the frozen 100/100 gate, but its run
  identity retained an obsolete human-readable geometry-method string. The run
  remains immutable and is superseded only for metadata provenance.
- `forest_v6_review_candidate02` reran the same frozen numerical gate after the
  metadata-only correction and passed 100/100. It is the delivered review
  candidate.

## Source and build checks

- Local pure-Python bridge suite: 64 tests passed after the mesh-support and
  trajectory-overlay changes.
- Remote targeted mesh-support suite passed 15 tests, followed by the full
  64-test Python bridge suite in the pinned Isaac Lab environment.
- Remote Foxy `scan_planner` rebuilt successfully after the endpoint latch;
  all six package tests passed, including the new latch regression. The two
  launch tests retain Foxy's known forced-shutdown diagnostic after their
  startup assertions but return success.
- Planner/optimizer, controller, Foxy bridge, and Isaac receiver all record a
  1.0 m/s forward ceiling; SCAN acceleration remains 0.5 m/s2.
- Shell syntax, Python byte compilation, JSON/YAML parsing, and
  `git diff --check` passed during qualification.

## Frozen candidate checks

- Automated report: PASS, 100 checks, zero failures.
- Physics duration: 29.660 s; policy rate: 50.000 Hz; sensor rate: 10.000 Hz.
- Goal error: 0.0393 m XY and 0.0183 m Z.
- Forward command: 0.999999 m/s; measured planar speed P75: 0.965667 m/s;
  low-yaw/high-command speed P75: 0.966764 m/s.
- Direct path is blocked; minimum root-to-tree-centre clearance is 0.830702 m;
  planned detour is 0.836485 m; path-length excess is 0.692684 m.
- Supported-contact fraction is 0.996631; maximum non-foot contact is 0 N;
  stopped command is 0 and stopped-motion maximum is 0.015586 m/s.
- Two complete SCAN B-splines are present. The overlay has 495 frames,
  2,675,638 bytes, SHA-256
  `3da16c44c258fed8209495d22b080071587387dfc389220844f8591b4d1ec8da`,
  and 15.970922 ms maximum plan/pose association error.
- Raw MP4 SHA-256 is
  `1ec64abffd5ef75200bd0f664bee8a33a6274ff2d54a52f8020621ebcf853858`.
- Frozen threshold SHA-256 is
  `5b74630b320cee5b606028aade73769cd2a76f86657d85eb794b10d7fdb95948`.

## Local evidence checks

- All 217 remote-produced files across the seven V6 result/log directories
  match their local copies. Sorted remote-manifest aggregate SHA-256:
  `c10ecad5190a3b52c1c4d4e7958975f008f27d2c1d82e42ea64bc64e67d92b94`.
- Fifty-one JSON files and 28 JSONL files (36,165 records) parsed; seven YAML
  files parsed; seven ROS bag SQLite databases passed integrity checks; seven
  NumPy depth arrays are finite; 26 PNG files decode.
- All 14 raw/overlay MP4 files fully decode. The final raw and overlay videos
  are regular H.264 files, 1280 x 720, 495 frames, and 29.117647 s.
- Local frozen-config re-evaluation is PASS. Its report differs from the
  Python 3.11 remote report only in the last 1.15e-14 of one path-length float
  under local Python 3.12; every boolean and threshold outcome is identical.

These checks establish a single-seed project-integrated Isaac/Foxy simulation
candidate. They do not establish Dr Sun's visual acceptance, Elevator-LIO,
calibrated MID-360/D435i parity, general forest robustness, or real-robot
safety.
