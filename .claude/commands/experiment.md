---
description: Experiment loop: show the experiment plan for confirmation, then decide whether to continue or stop after each result.
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**

You are the Lite3 quadruped navigation DRL Experiment Driver. Experiments must not start blindly; every round needs confirmation.

## Step 1: Read Current State

```text
bigmemory/热区/状态简报.md
.pipeline/experiments/                  # Existing experiment ledgers, to avoid repeating failed configs.
.pipeline/terminology/terminology.md
```

Use `AskUserQuestion` to show the current experiment context:

> **Current state**: [extract from state brief]
> **Existing experiments**: [number of .pipeline/experiments/ ledgers, or "none yet"]
>
> Ready to enter the experiment loop. The first step is experiment-plan design.

Options:
- `Continue, design plan first`
- `I will describe the experiment config I want`
- `Cancel`

If the user describes a config, record it before entering design.

## Step 2: Design Experiment Plan

Design the experiment plan from `bigmemory/热区/状态简报.md` and historical ledgers under `.pipeline/experiments/`, avoiding repeated failed configs.

Use `AskUserQuestion` to show a plan summary and wait for confirmation:

> **Experiment plan**:
> - Objective: [hypothesis to verify]
> - Config: use the baseline-specific config location recorded in that baseline's `CURRENT_CODE.yaml`.
> - Algorithm: PPO / SAC
> - Simulation environment: Isaac Lab / MuJoCo
> - Evaluation metrics: ...
>
> After confirmation, implementation and execution start.

Options:
- `Plan is okay, start implementation`
- `Adjust one config`
- `Redesign plan`

## Step 3: Implement and Run

Write code changes under `2_experiment/nav_baselines/<topic>/` or the nav subproject directory specified by the Contract. If reusing a walking base policy, record source repo, commit, checkpoint, and freeze/fine-tune boundary in both the Contract and ledger. Execute through `/delegate` or a remote task package.

For remote execution, follow the common command template in `.claude/rules/experiment.md`.

## Step 4: Record Experiment Ledger

After each experiment run, create a ledger `YYYYMMDD_<topic>.md` under `.pipeline/experiments/`, following `.claude/agents/experiment-driver.md`.

Use `AskUserQuestion` to ask Dr Sun for human observations:

> **Experiment [topic] has been recorded at `.pipeline/experiments/YYYYMMDD_<topic>.md`**
>
> Please add your human observations, such as training-curve trend, anomalies, or intuition:

Options:
- `I will write notes`
- `Skip for now; add later`

## Step 5: Evaluate Results and Decide Next Step

Use `AskUserQuestion` to show results:

> **Latest experiment result**: [key metrics]
> **Status**: passed / not passed

Options when not passed:
- `Adjust hyperparameters and run another round`
- `Change experiment design and restart`
- `Result is enough, move to writing`

Options when passed:
- `Go to /write for paper writing`
- `Run more comparison experiments`

## Reminders

- **Baseline first**: before new experiments, reproduce the baseline to establish a reliable anchor. Keep baseline reproduction separated from new experiment development when possible.
- **Data version lock**: all models use exactly the same preprocessed data; random seeds are explicit and recorded.
- **Error bars**: when feasible, run multiple trials and report mean +/- standard deviation. A single run is weak evidence.
- **Contract check**: before experiments, check whether `.pipeline/contracts/` has the corresponding Research Contract. See hard rule #20 and `.claude/rules/experiment.md`.
