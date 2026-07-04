---
description: Conductor plans a task and spawns a codex:codex-rescue subagent for background execution (mode B).
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**
> **This command is disabled as the default Codex path in Cursor**: in Cursor, use `/delegate-offline` style and only generate a prompt for Dr Sun to manually input into Codex.

You are the Lite3 quadruped navigation DRL Conductor. This command **delegates code or experiment tasks to Codex**. The main Claude session only plans and integrates results, saving Opus tokens (mode B).

## Step 1: Read Context

```text
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
.pipeline/experiments/
.pipeline/terminology/terminology.md
```

## Step 2: Show Plan and Wait for Confirmation

Use `AskUserQuestion` to show Dr Sun the task summary to be delegated:

- **Task**: 1-2 sentence description of what Codex will do.
- **Context injection**: AGENTS.md automatically provides hard rules and terminology; list extra prompt context.
- **Output location**: where Codex should write outputs.

Options:
- `Confirm, spawn subagent`
- `I will adjust the task description`
- `Cancel`

## Step 3: Spawn codex:codex-rescue Subagent Only After Confirmation

Call the Agent tool with:

- `subagent_type`: `codex:codex-rescue`
- `description`: <=6-character task summary
- `prompt`: complete task description, including:
  - project context extracted from the state brief
  - experiment code must declare a Python module by nav baseline subproject; default directory is `2_experiment/nav_baselines/<topic>/`
  - if a walking base policy is reused, state source repo, commit, checkpoint, and freeze/fine-tune boundary
  - experiment directory `2_experiment/`
  - titles and conclusions from the latest 3 ledgers under `.pipeline/experiments/`, to avoid repeats
  - task description
  - output requirements: code changes under the matching nav subproject directory; experiment ledger `.pipeline/experiments/YYYYMMDD_<topic>.md`; follow `.pipeline/terminology/terminology.md`
- `run_in_background`: `true` so the subagent runs in the background and the main session can continue; the system will notify when done.

## Step 4: Wait for Completion and Read Results

After the subagent returns, read its summary and check persisted outputs:

```bash
ls .pipeline/experiments/ | tail -5
git log --oneline -5
```

Briefly tell Dr Sun what was done, which files were produced, and whether there are issues.

Use `AskUserQuestion`:
- `Accept result, continue next step`
- `Need changes somewhere`
- `This result is wrong; discard`

## When To Use /delegate-offline

If Dr Sun needs to watch Codex output in an independent terminal for debugging, interaction, or long training, or if the current CLI is Cursor, use `/delegate-offline`; it only generates a prompt for Dr Sun to run with the independent `codex` CLI.
