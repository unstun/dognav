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
`office-r2.0.0-preflight`, its presentation template is
`office-dualview-v1.0.0`, and both `accepted_revision` and `formal_candidate`
remain null. The source snapshot is backed by commit `f320db3c356a` on branch
`codex/office-r2-mid360-preflight-archive`; runtime artifacts remain local and
the revision is neither accepted nor formal.

The source-backed MID-360 sensor qualification and
`office_crowd_mid360_dualview_preflight02` are limited smoke/preflight evidence.
The latter is a 10.04-second visual preview: its presentation and same-run native
RViz synchronization checks passed, but it did not reach the goal, the
full-duration pedestrian gate is `NOT_GATED`, it is not a new complete AC54
run, and it cannot satisfy AC55 or formal validation. It does not replace
candidates 38 or 39.

Before a behavior-changing run, record the parent implementation, motivation,
exact change, expected signals, failure signals, command, local source commit,
and artifact destination. Append results after the run; do not rewrite
pre-run expectations.
