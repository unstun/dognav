# V5 Verification Record

Status: automated checks passed; human video review is still pending.

## Source checks

- Local pure-Python suite: 54 tests passed.
- Remote Foxy `scan_planner` build: package completed successfully in the
  pinned rootless Foxy container.
- Remote `scan_planner` CTest: three test targets passed (trajectory-progress
  gtest plus two launch tests). The Foxy launch harness still emits its known
  forced-shutdown warning after startup assertions; the package tests return
  success, and the uninterrupted V5 runtime exits all four ROS nodes cleanly.
- Remote Foxy `lite3_sim_bridge` build: package completed successfully.
- Remote bridge pytest: 54 tests passed, including the stale-backlog/fresh-
  latest regression.
- Shell syntax and ShellCheck passed for the common and V5 runners.
- Python byte compilation, JSON parsing, YAML parsing, and source/document
  `git diff --check` passed. Raw simulator/ROS logs retain their original
  trailing whitespace and are intentionally excluded from that formatting
  check. No temporary `[DEBUG-v5transport]` instrumentation remains in source;
  its three timing lines remain only in the preserved diagnostic log.

## Cross-layer checks

- Goal identity is `[0.5, 3.0, 0.85]` in the planner config, frozen threshold,
  and executed run identity.
- Planner, optimiser, and controller forward limits are all `0.50 m/s`; the
  independent transport/policy clamp remains `[0.75, 0.35, 1.0]`.
- The executed sensor identity declares rendered world XYZ plus sensor pose as
  filter inputs and forbids terrain height, prim IDs, proxy bounds, and labels.
- The frozen local acceptance rerun contains 86 passing checks and is byte-
  identical to the copied remote report.

## Artifact checks

- Local/remote durable trees: 145 files, identical aggregate SHA-256
  `48b3275971a0171d1f79d44b3fb81bcc6482457bdba2d46d1faa7015fa938289`.
- Structured data: 50 JSON/JSONL files parsed.
- ROS bags: five SQLite databases passed `pragma quick_check`.
- Depth: five finite NumPy arrays loaded with shape `58 x 87`.
- Video: five H.264 MP4 files fully decoded. The frozen candidate is 1280 x
  720, 438 frames, 25.764706 s, and 11,143,074 bytes.

These checks establish an automated simulation review candidate, not Dr Sun's
visual acceptance, calibrated sensor parity, localization performance, or
real-robot safety.
