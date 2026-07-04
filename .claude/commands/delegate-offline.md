---
description: Generate a prompt for an independent Codex terminal; Dr Sun copies it into a new terminal and runs codex CLI (mode A).
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**

You are the Lite3 quadruped navigation DRL Conductor. This command **generates a Codex prompt for Dr Sun to run in an independent terminal** (mode A). Use it when:

- Dr Sun needs to observe Codex output in real time, for debugging or interactive work.
- The task is long-running and should not occupy the main Claude session.
- The task does not need to stream back into the main context.

## Step 1: Read Context

```text
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
.pipeline/experiments/
.pipeline/terminology/terminology.md
```

## Step 2: Show Plan and Wait for Confirmation

Use `AskUserQuestion` to show:

- **Task**: 1-2 sentence description.
- **Context injection**: `AGENTS.md` is loaded automatically by Codex CLI; list any extra information included in the prompt.
- **Output location**: where Codex should write outputs.

Options:
- `Confirm, generate prompt`
- `I will adjust the task description`
- `Cancel`

## Step 3: Generate Codex Prompt Only After Confirmation

Show the complete command in a code block:

```text
In a new terminal, cd to the project root (/Users/sun/tongbu/study/phdproject/machine-dog-nav), then run:

codex "[complete prompt]"
```

If background execution is needed, Dr Sun may run `nohup codex "..." &` or keep it in a separate tmux/terminal. The local `codex` CLI has no `--background` flag. In Cursor, Codex should use this command/mode by default; do not call the `codex-rescue` plugin.

Complete prompt format:

```text
[Project context]
Research topic: Lite3 quadruped navigation DRL (extract from state brief)
Experiment code: declare a Python module by nav baseline subproject; default directory is `2_experiment/nav_baselines/<topic>/`.
If a walking base policy is reused, state source repo, commit, checkpoint, and freeze/fine-tune boundary.
Experiment directory: 2_experiment/

[Existing experiment records - avoid repeats]
(titles and conclusions of the latest 3 ledgers under .pipeline/experiments/)

[Your task]
(confirmed task description)

[Output requirements]
- Write code changes under the matching nav subproject directory.
- After the experiment ends, create a new ledger at .pipeline/experiments/YYYYMMDD_<topic>.md
- Follow terminology rules in .pipeline/terminology/terminology.md
```

## Step 4: Wait for Dr Sun to Confirm It Is Running

Use `AskUserQuestion`:
- `I have started it in a new terminal`
- `Cancel`

## Step 5: Wait for Completion and Read Results

After Dr Sun confirms completion, check outputs:

```bash
ls .pipeline/experiments/ | tail -5
git log --oneline -5
```

Briefly explain the outputs to Dr Sun.

Use `AskUserQuestion`:
- `Accept result`
- `Need changes somewhere`
- `This result is wrong; discard`

## When To Use /delegate Instead

Only in Claude Code / Droid, if the task does not need Dr Sun to watch Codex output in real time and only needs execution plus a result summary, use `/delegate`; it spawns the `codex:codex-rescue` subagent in the background. **Do not switch to `/delegate` in Cursor**: keep generating a prompt for Dr Sun to manually input into Codex.
