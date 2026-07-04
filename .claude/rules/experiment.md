---
paths: ["2_experiment/**", "configs/**"]
---

# Experiment Rules

## Hard Rules

- MUST: training/inference parameters belong in the matching nav baseline subproject's `configs/` directory, or in the location explicitly specified by the Contract.
- MUST: after ablation experiments finish, record them in `.pipeline/experiments/`.
- MUST: before remote training/inference, sync code completely. If temporary remote edits happen, sync them back to the same local paths before finishing and show them through local `git diff`. A remote-only state where remote runs succeed but local code has no counterpart is forbidden.
- MUST: before inference, confirm the checkpoint file is correct; do not rely on "default latest".
- MUST: remote SSH conda execution must use `conda run --cwd <absolute-project-path>/2_experiment -n <env> python ...`.
- MUST: experiment code declares a Python module by nav baseline subproject. Default directory: `2_experiment/nav_baselines/<topic>/`. When reusing external or walking code, record the source under `2_experiment/source_references/<name>/_meta/`.

## Environment

| Platform | Purpose | Notes |
|---|---|---|
| Mac (Apple Silicon) | code development / paper writing | PyTorch CPU build; `KMP_DUPLICATE_LIB_OK=TRUE` is set |
| Ubuntu (remote GPU) | training + inference | RTX 4090, Isaac Lab / MuJoCo |

## Common Command

```bash
PROJ=$HOME/machine-dog-nav; EXP=$PROJ/2_experiment; ENV=<conda_env>

# Entry goes through the nav baseline subproject module:
mkdir -p "$EXP/runs"
nohup conda run --cwd $EXP -n $ENV python -m <nav_module>.cli.train \
  --profile $PROFILE \
  > $EXP/runs/${PROFILE}_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

## Stage Order

Experiment progress must follow this order. Do not skip steps:

1. **Baseline reproduction** -> establish a reliable anchor.
2. **Research Contract** -> lock hypothesis and success/failure signals (hard rule #20).
3. **Experiment execution** -> judge results against the Contract.

## Baseline Reproduction

- MUST: before experiments, check existing datasets and environment docs instead of blindly re-downloading.
- MUST: run reproduction through a subagent; the main session receives only the result summary.
- MUST: after reproduction succeeds, record it in `.pipeline/experiments/` so it becomes the anchor for later experiments.

## Pre-Experiment Checks

- Check stage order: baseline reproduced -> Contract submitted.
- Check whether `.pipeline/contracts/` contains the corresponding Research Contract (hard rule #20).
- Check whether the dataset already exists in known paths.
- Check whether the environment has been set up.
