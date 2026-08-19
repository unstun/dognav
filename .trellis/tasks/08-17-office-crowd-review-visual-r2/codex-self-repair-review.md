# Codex Self-Repair Review — 2026-08-18

## Scope and claim boundary

- Stage: experiment + analysis.
- `candidate38` and `candidate39` remain immutable and were not used as output
  targets.
- This review covers the short visual preflight
  `office_crowd_review_preflight15`; it is not AC54/AC55 evidence and does not
  authorize a formal candidate.
- AC55 remains pending Dr Sun's explicit visual decision.

## Result submitted for human review

- All four presentation videos are 1920x1080, 25 fps, H.264 High, yuv420p,
  BT.709, TV range, with 376 fully decoded frames each.
- The strict local presentation validator returned `passed: true` with no
  issues. It verified camera/state trace parity, video distinction, material
  audit, genuine XYZ plan/root/occupancy provenance, and mandatory input hashes.
- The complete local bridge suite passed 93/93 tests. Shell syntax, shellcheck,
  Python compilation, and owned-path `git diff --check` passed.
- The 37 remote evidence files and their local copies have identical recursive
  SHA-256 manifests.

## Video SHA-256

- `closed_loop.mp4`:
  `3a24463ae9537ae557a121c52a3a8ef83a104e3b448708fd069b8fd36498b6dd`
- `closed_loop_third_person_side.mp4`:
  `e0313e6dca6c245e2ffe32aeb4dcbd911766550766d90a6ccb1198b7a6656199`
- `closed_loop_overview.mp4`:
  `83561a7b4184c5980a6378a49f20cc89837b57f7b2ffe0ef6f65e5d6457452b8`
- `office_review_dashboard.mp4`:
  `dd5fe09501de06d274b6c5d4df0bd524714bd59f17d55179c3b8de14723d93a4`

## Independent visual review

- The orange torso and graphite limbs remain legible against the Office floor.
- The side observer is a genuine external camera and follows the robot without
  simulator stepping between camera renders.
- The overview camera is distinct from the side observer and keeps the robot
  and surrounding Office context visible.
- The dashboard shows three synchronized cameras plus a true XYZ isometric
  planned/root/occupancy panel.
- Known limitation disclosed for human review: the compatibility first view has
  a brief furniture/bright-surface obstruction near the beginning. Attempts to
  hide it with a high fallback (`preflight16`) or a distance blend
  (`preflight17`) were rejected because they introduced an overhead view or
  further camera traversal. Both failed preflights are preserved unchanged.

## Gate status

- Automated presentation preflight: pass.
- Human visual gate AC55: pending.
- Full dry runs / formal candidate / archive / commit: not performed.
