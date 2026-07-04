---
name: evidence-grounded-training-modification
version: 1.0.0
description: |-
  Use before modifying machine-dog-nav training algorithms, reward functions, terrain curriculum,
  PPO behavior, evaluation rules, or diagnostics. Requires every substantive training change
  to be grounded in local primary evidence: checked-out GitHub repositories, local PDFs, or
  extracted paper text stored inside the project.
argument-hint: "[training change or experiment being considered]"
user-invocable: true
---

# Evidence-Grounded Training Modification

Use this skill before changing training algorithms, terrain curriculum, reward terms,
PPO behavior, evaluation pass rules, or diagnostic metrics.

## Rule

Every substantive training change needs a local source anchor before editing:

1. Prefer checked-out source repositories under `2_experiment/source_references/<name>/upstream/`.
2. Prefer local PDFs under `1_survey/papers/`.
3. Convert relevant PDFs to searchable text under `.pipeline/experiments/<date>_*_reference_extracts/`.
4. Record exact files, line numbers, commit hashes, and the intended code change in an experiment note.

Instrumentation-only changes may use the current project code as the source anchor, but the note still needs to say that the change only records metrics and does not alter training behavior.

## Workflow

1. Classify the change:
   - algorithm or reward change;
   - terrain or curriculum change;
   - PPO or action-distribution change;
   - evaluation or success-rate change;
   - diagnostics-only change.
2. Find local evidence:
   - walking base repo snapshot for locomotion source semantics;
   - Isaac Lab clone for simulator API behavior;
   - RSL-RL or legged-gym source for PPO/curriculum conventions;
   - local PDF text for paper-level method and evaluation claims.
3. Compare source and current implementation before editing.
4. Make the smallest code change that follows the evidence.
5. Save a short experiment note with:
   - source files and lines;
   - current code files and lines;
   - changed files;
   - verification commands;
   - remaining uncertainty.
6. Commit the change and the note together.

## Current Local Anchors

Use these first for nav work once they exist:

```text
1_survey/papers/<CitationKey>.pdf
2_experiment/source_references/<walking_base>/_meta/SOURCE_SNAPSHOT.yaml
2_experiment/source_references/<isaaclab>/upstream/
2_experiment/source_references/<nav_baseline>/upstream/
```

Current extracted text location:

```text
.pipeline/experiments/<YYYY-MM-DD>_<topic>_reference_extracts/
```
