# Experiment Records

Navigation experiments, integration smokes, and visual preflights now exist.
The main record groups are:

- `2026-08-13_scan_foxy_isaac_closed_loop/`: the Foxy/Isaac closed-loop base;
- the dated forest and indoor preview/review directories from 2026-08-14 through
  2026-08-16; and
- `2026-08-17_office_l0_scan_crowd/`: the current Office L0 crowd experiment,
  including its report, change control, revision ledger, and immutable results.

For the Office experiment, candidates 38 and 39 remain the immutable same-input
evidence that passed the declared automated AC51--AC54 gate. AC55 remains a
human gate owned by Dr Sun. The current working revision is
`office-r2.0.1-preflight`, parent `office-r2.0.0-preflight`; its only change
group is `golden_dualview_delivery_reliability`. The presentation layout remains
the frozen `office-dualview-v1.0.0` template, while its persistence/audit and
transfer-delivery contract is `office-dualview-v1.0.1`. Both
`accepted_revision` and `formal_candidate` remain null. The normalized parent
snapshot is backed by commit `f320db3c356a` on branch
`codex/scan-foxy-isaac`; archive commit `6dba7c2` and the canonical local
experiment paths now contain the MID-360 and golden dual-view evidence. Large
videos remain local-only by repository policy, with hashes and textual evidence
kept in Git. The historical revision is neither accepted nor formal.

The current unaccepted build is `office-v2.0.1-go2-geometry-preflight`, with
the independent `upstream_go2_reference` profile. It splits each genuine scan
into `/quad_0/cloud_raw` for persistent RViz display and `/quad_0/cloud` for
SCAN, and borrows only the five pinned Go2 collision-envelope values. Flat
short-preflight run 01 is retained as failed; run 02 produced 101/101 paired
scan audits and verified master/transfer videos after preserving two
postprocessing failures. Non-flat simulation still requires Dr Sun's separate
approval, so the result is not complex-terrain validation.

The source-backed MID-360 sensor qualification and
`office_crowd_mid360_dualview_preflight02` are limited smoke/preflight evidence.
The latter is a 10.04-second visual preview: its presentation and same-run native
RViz synchronization checks passed, but it did not reach the goal, the
full-duration pedestrian gate is `NOT_GATED`, it is not a new complete AC54
run, and it cannot satisfy AC55 or formal validation. It does not replace
candidates 38 or 39.

`office_crowd_r2_0_1_live_cloud_transfer_preflight06` is the latest 10.04 s
delivery-reliability preflight. It observes 96 of 101 genuine generated clouds
(0.950495 coverage), finds no ROS-stamp regression, measures a 0.2 s maximum
simulator-time receipt gap, and finds the cloud visible in all 251 delivered
video frames. Its CRF 26 transfer entity is 11,543,483 bytes versus a
58,781,800-byte master (80.36% smaller), fully decodes, and has SSIM 0.974314.
Attempts 01--05 remain immutable failures. This is automated short-preflight
evidence pending Dr Sun's visual review; it does not reach the goal, rerun AC54,
decide AC55, or authorize a formal candidate.

Before a behavior-changing run, record the parent implementation, motivation,
exact change, expected signals, failure signals, command, local source commit,
and artifact destination. Append results after the run; do not rewrite
pre-run expectations.
