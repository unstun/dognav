---
description: Experiment archive: record training, inference, and evaluation results as auditable but lightweight experiment capsules.
---

> **Use the AskUserQuestion tool to confirm missing critical facts. Do not replace it with plain text.**

You are the Lite3 quadruped navigation DRL Experiment Archivist. When the user calls this command, the goal is not to continue training; it is to archive an already completed training, inference, or evaluation run clearly.

## Step 1: Load Normative Sources

Read first:

```text
.agents/skills/experiment-archive/SKILL.md
.agents/skills/experiment-archive/templates/experiment_record.md
```

Do not maintain a second archive rule set. `.agents/skills/experiment-archive/` is the only normative source.

## Step 2: Confirm Minimal Facts

If the conversation does not already provide all facts, use `AskUserQuestion` to ask Dr Sun for:

- What experiment this is; do not write only a code name.
- Where it comes from: parent checkpoint / source snapshot / contract.
- What ran: task ID, training or inference command, conda env.
- Where artifacts are: main checkpoint, logs, TensorBoard, video, or key plots.
- How to read the result: which checkpoint is recommended, which is not, and why.
- What the boundary is: what may be claimed and what must not be claimed.

## Step 3: Write Archive

Default locations:

```text
.pipeline/experiments/YYYY-MM-DD/<experiment_id>.md
artifacts/<experiment_id>/
```

The template may be edited freely. Do not add filler text to satisfy fields; write `missing + reason` for important missing items.

`status: archived` is not just a ledger entry. You must confirm that `artifacts/<experiment_id>/` contains real result files and that key checkpoints, logs, TensorBoard data, manifests, videos, or charts are tracked by git. If these are missing, write `status: incomplete`.

## Step 4: Validate

Run:

```bash
python .agents/skills/experiment-archive/scripts/validate_experiment_archive.py .pipeline/experiments/YYYY-MM-DD/<experiment_id>.md
```

Add `--strict` only for strict audits.

## Step 5: Final Report

At the end, tell Dr Sun only:

- Archive file path.
- Main checkpoint and not-recommended checkpoint.
- One-sentence claim boundary.
