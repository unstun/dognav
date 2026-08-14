# Human Review Gate

Status: **PENDING — V3 AUTOMATED GATE PASSED, HUMAN DECISION REQUIRED**

`acceptance_v3_frozen` passed all 71 frozen automated checks. This does not
satisfy AC17. Agent inspection, image crops, hashes, and numerical checks are
supporting evidence only; Dr Sun must review the complete V3 video and record
an explicit accept or reject decision before the task can be archived.

## Primary V3 Review Artifacts

1. Full formal-run video:
   `runs/acceptance_v3_frozen/results/acceptance_v3_frozen/closed_loop.mp4`
2. Sensor-rig close-ups:
   `runs/acceptance_v3_frozen/review_frames/02s_sensor_rig_closeup.png`,
   `10s_sensor_rig_closeup.png`, and `15s_sensor_rig_closeup.png`
3. D435i depth preview:
   `runs/acceptance_v3_frozen/review_frames/d435i_depth_preview_8x.png`
4. Frozen automated report:
   `runs/acceptance_v3_frozen/results/acceptance_v3_frozen/acceptance_report.json`
5. Independent local re-evaluation:
   `runs/acceptance_v3_frozen/local_acceptance_recheck.json`
6. Frozen thresholds: `acceptance_thresholds_v3.json`
7. Asset/runtime readback:
   `runs/acceptance_v3_frozen/results/acceptance_v3_frozen/isaac/runtime_composition.json`
8. V12 old/new asset comparison:
   `gates/v3_asset_sensor_qualified/v12_asset_ab_report.json`
9. Local/remote parity:
   `runs/acceptance_v3_frozen/local_results_sha256.txt`,
   `remote_results_sha256.txt`, `local_logs_sha256.txt`, and
   `remote_logs_sha256_absolute.txt`
10. Concise evidence index:
    `runs/acceptance_v3_frozen/V3_EVIDENCE_MANIFEST.md`

The MP4 is intentionally ignored by Git but is a regular local file. Its
expected SHA-256 is
`db230a6e5460c8db09a95a1742f435169bf4e32fbdc4f980ba085afc3903d26d`.

## Visual Review Checklist

- [ ] The new top sensor-rig geometry is present throughout the V3 video; this
  is not the legacy bare V12 URDF.
- [ ] The Lite3 advances through articulated leg motion rather than base
  teleportation or planar pose integration.
- [ ] The robot goes around the physical red obstacle without visible contact,
  clipping, or pass-through.
- [ ] Body attitude and foot contacts remain plausible through the detour.
- [ ] The robot continues toward the declared goal and settles without a scene
  cut, hidden reset, or stale-command motion.
- [ ] The separate D435i preview contains a finite scene-derived depth image
  and a visible obstacle region; it is not a static illustration.

## Evidence Review Checklist

- [ ] `acceptance_v3_frozen` reports `PASS`, contains 71 checks, and contains no
  failed check.
- [ ] The canonical and Isaac-safe URDF hashes are respectively
  `d0a1be09...cec80` and `803d5527...bb9d`.
- [ ] Runtime readback reports 24 bodies, 23 joints, 12 movable joints,
  11 fixed joints, 29 collision prims, and approximately 13.281789 kg total
  mass without a silent default-mass body.
- [ ] The V12 checkpoint remains `model_149999.pt` with SHA-256
  `a9d31dce...3d5450`; the A/B comparison does not attribute observed deltas
  to one payload component without evidence.
- [ ] The MID-360-like stream is bound to `mid360_scan_frame` and the D435i-like
  stream is bound to `d435i_depth_optical_frame`.
- [ ] Local and remote result hashes match, and a fresh local evaluation also
  reports 71/71 PASS.
- [ ] V1/V2 evidence remains preserved and V2 is labeled baseline-only.
- [ ] The report states simulator-truth pose, geometric ray-cast sensors, one
  fixed seed, and one flat single-obstacle course. It does not claim hardware
  parity, LIO, a trained navigation policy, or real-robot safety.

## Human Decision

- [ ] **Accept** V3 as the reviewed fixed-course simulation baseline.
- [ ] **Reject / request changes** before this task is archived.

Reviewer:

Date:

Notes:
