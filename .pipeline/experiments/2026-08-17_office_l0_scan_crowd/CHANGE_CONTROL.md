# Office L0 Change and Version Control

This file defines the human-readable control plane for the Office L0 crowd
experiment. The machine-readable current state lives in
`revision_ledger.json` and is checked by `validate_revision_ledger.py`.

## Identities That Must Not Be Mixed

- **Revision**: a source/configuration state, such as
  `office-r2.0.0-preflight`.
- **Run ID**: one immutable execution of one revision. A retry always receives
  a new run ID.
- **Candidate**: a run promoted only after its declared automated gates pass.
- **Human decision**: Dr Sun's explicit visual acceptance or rejection. This is
  separate from automated acceptance and cannot be inferred from a PASS file.
- **Presentation contract**: a frozen layout or rendering convention. The
  golden dual-view template can be frozen without accepting the navigation
  candidate shown inside it.

## Revision Format

Use `office-rMAJOR.MINOR.PATCH[-qualifier]`.

- Increment `MAJOR` when the scientific claim, planner/sensor interface, route,
  acceptance protocol, or evidence contract changes.
- Increment `MINOR` for exactly one planned behavior change inside the same
  claim boundary.
- Increment `PATCH` for exactly one instrumentation, validation, packaging, or
  presentation repair that does not change navigation inputs.
- Use `-preflight` until the source is frozen and the required full gates pass.

`office-r2.0.0-preflight` is a normalization snapshot of the current accumulated
work, not a claim that all earlier edits were historically one change group.
Every revision created after this snapshot must contain exactly one declared
change group.

## Run ID Format

New Office runs use:

```text
office_crowd_r<major>_<minor>_<patch>_<purpose>_<stage><NN>
```

Allowed stages are `smoke`, `preflight`, `dryrun`, and `candidate`. Existing
legacy run IDs remain immutable and are mapped to a revision or explicitly
marked `legacy_unversioned`; they are not renamed or retroactively rewritten.

## Required Iteration Card

Before editing or running, update `revision_ledger.json` with:

1. parent revision and new revision;
2. one change group and its rationale;
3. exact allowed components and frozen invariants;
4. expected artifacts and validation gates;
5. claim boundary and actions that remain unauthorized;
6. planned run ID before remote execution.

After execution, append the immutable run result, evidence paths and hashes,
automated status, human status, and next authorized action. Never replace a
failed run entry or move its files.

## Promotion Rules

```text
draft
  -> locally_verified
  -> remote_smoke_passed
  -> visual_preflight_passed
  -> human_preflight_review_pending
  -> full_dryrun_authorized
  -> formal_candidate_automated_passed
  -> human_accepted
```

`failed`, `rejected`, and `superseded` are immutable terminal run outcomes.
They do not erase evidence. A revision may have multiple run attempts only when
the revision inputs are unchanged. Any source, config, scenario, gate, or
presentation-contract change creates a new revision first.

## Current Boundary

- Frozen automated baseline: candidate38 and candidate39, AC54 PASS under their
  historical inputs, AC55 still pending.
- Frozen presentation baseline: `office-dualview-v1.0.0`, high external
  third-person at left and simulator-time synchronized native 5070 Ti RViz at
  right, 1920 x 1080 per panel. The current instrumentation/delivery patch is
  `office-dualview-v1.0.1`; it does not change that layout.
- Current working revision: `office-v2.0.1-go2-geometry-preflight`, parent
  `office-r2.0.1-preflight`, with the single change group
  `dual_cloud_transport_and_upstream_go2_geometry_reference`. The system
  version remains `v2.0.1`; the `v` spelling identifies this new build and
  does not rewrite the historical `r2.0.1` archive.
- Canonical archive: source snapshot `f320db3c356a`, state archive `6dba7c2`,
  branch `codex/scan-foxy-isaac`. The referenced result directories are present
  at their canonical local paths and hash-verified; large binary entities remain
  local-only under repository policy while their hashes and textual evidence
  are Git-backed.
- First new-profile run `office_v2_0_1_go2_geometry_preflight01` is an
  immutable failed short preflight: its 1 s telemetry receive timeout caused
  reconnects and missing Foxy scan audits, and the full-duration pedestrian
  gate was incorrectly applied to a 10 s preview. Run
  `office_v2_0_1_go2_geometry_preflight02` is the first flat 10.04 s short
  preflight with 101 generated and 101 audited dual-cloud scans. Its original
  postprocessor failed because it imported a stale module; both failed retries
  are preserved and the corrected retry records PASS without rerunning or
  overwriting the simulation.
- The navigation inputs are unchanged: MID-360 stays at 10 Hz simulator time,
  20,000 ordered rays per scan, 0.1--40 m, with the pinned pattern and same-step
  stamp. Each scan now yields ground-inclusive `/quad_0/cloud_raw` for Decay-0
  RViz and geometry-filtered `/quad_0/cloud` for SCAN. No scan is replayed,
  duplicated, interpolated, or classified with scene labels.
- The separate `upstream_go2_reference` profile borrows only radius 0.25 m,
  offset 0.18 m, body height 0.40 m, and 0.10 m z inflation above and below
  from SCAN-Planner commit `348e8a590a50a5a6bbab8d8c6dcfd171f009be26`.
  These are Go2 reference values, not Lite3 calibration. Go2's 0.75 m/s speed
  was not copied; Lite3 remains at 0.50 m/s.
- Dr Sun authorized the 60-second flat dry run on 2026-08-31. Immutable
  `dryrun01` failed during delivery packaging; detached `dryrun02` passed the
  declared full-duration flat gates and produced preserved 4K, standard, and
  9,176,726-byte review entities. That authorization is consumed.
- `accepted_revision` and `formal_candidate` remain null. AC54 was not rerun,
  AC55 remains pending, and non-flat or formal-candidate work requires fresh
  explicit authorization after Dr Sun reviews the full-duration video.
- Non-flat simulation remains separately unauthorized. Static slope, step, and
  sparse-cloud tests plus SCAN route-height GTests do not validate Lite3 complex
  terrain capability.
