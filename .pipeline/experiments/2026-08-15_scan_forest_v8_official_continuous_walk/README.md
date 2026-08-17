# Official Human Continuous-Walk Preview

This auxiliary preview keeps the frozen Lite3, forest, SCAN, dynamic-obstacle
schedule, speed, physical capsule, and sensor inputs unchanged. The only variant
is `official_human_animation_mode=continuous_walk`: the pinned official NVIDIA
walk clip loops during waiting, crossing, holding, and parked phases.

This is a visual-review experiment, not an acceptance run. It does not replace
the phase-conditioned candidate or close the final human-review gate.

Run on the pinned 5070 Ti execution copy:

```bash
./run_remote_continuous_walk_preview.sh RUN_ID DURATION_SECONDS TELEMETRY_PORT COMMAND_PORT
```

Expected review artifacts are `closed_loop.mp4`,
`closed_loop_review_overlay.mp4`, `isaac/metrics.jsonl`, and
`effective_input.txt` under the run result directory.

## Preview 01

`v8_official_continuous_walk_preview01` completed on the RTX 5070 Ti execution
copy with Isaac and the Foxy container both exiting zero. The local source and
remote execution files were SHA-256 identical before launch.

- requested wall duration: 16 s;
- rendered video: 203 frames, 1280 x 720, 17 fps, 11.94 s;
- runtime rows: 607;
- clip selection: 607 `walk`, zero `idle`;
- covered physical phases: waiting 15, crossing 175, holding 125, parked 292;
- distinct walk frames: crossing 90, holding 76, parked 90;
- non-foot contact maximum: 0 N;
- closest reported robot-to-human proxy surface clearance: 0.108 m.

The run intentionally has no acceptance report. The numeric checks only prove
that continuous-walk mode was applied and the preview completed; visual quality
remains a human-review decision.

Video SHA-256:

- raw: `3e99b8958f430d5e934af3668fe3fa999b7bbb1e1528c73934db9939b37b1362`;
- overlay: `23b43fb8042ac98d9730ec994a4078290c49c96cf8673c8b6cf75b898d525591`.
