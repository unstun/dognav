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
- Frozen presentation template: `office-dualview-v1.0.0`, high external
  third-person at left and simulator-time synchronized native 5070 Ti RViz at
  right, 1920 x 1080 per panel.
- Current working revision: `office-r2.0.0-preflight`, containing the
  source-backed MID-360 input and the frozen dual-view presentation contract.
- Canonical archive: source snapshot `f320db3c356a`, state archive `6dba7c2`,
  branch `codex/scan-foxy-isaac`. The referenced result directories are present
  at their canonical local paths and hash-verified; large binary entities remain
  local-only under repository policy while their hashes and textual evidence
  are Git-backed.
- Latest run: `office_crowd_mid360_dualview_preflight02`, a 10-second visual
  preflight only. It did not reach the goal, did not run the full-duration
  pedestrian fraction gate, did not rerun AC54, and cannot satisfy AC55.
- Next action: wait for Dr Sun's visual decision. Full dry runs and a formal
  candidate require a fresh explicit authorization.
