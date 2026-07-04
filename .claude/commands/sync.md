---
description: Force-sync project state into the bigmemory hot zone and .pipeline knowledge base.
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**

You are the Lite3 quadruped navigation DRL Conductor. The user calls this command because project state documents are stale. Your task is to **fully refresh hot-zone state and complete the knowledge base**.

## Step 1: Read All Raw Data

Read all state sources at once to get complete context:

```text
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
bigmemory/热区/近期改动.md
.pipeline/literature/index.md
.pipeline/experiments/                    # Scan all ledger files.
.pipeline/survey/                         # Scan all survey files.
.pipeline/terminology/terminology.md
3_paper/main.tex                          # Current paper state.
2_experiment/nav_baselines/               # nav baseline subprojects.
2_experiment/source_references/           # walking / external source references.
```

## Step 2: Ask User About Missing Progress

Use `AskUserQuestion`:

> **Progress sync**
>
> I have read all files and am ready to update state documents.
>
> Please briefly describe any work that is actually complete but not recorded in the documents, if any:
> - Example: "PPO baseline training completed, success rate 78%"
> - Example: "Changed terrain generation to procedural random forest"
> - Example: "Nothing missing; the documents are just stale"

Options:
- `Nothing missing; sync from existing files`
- `Something is missing; I will describe it`

If the user chooses "something is missing", ask in plain text for concrete details, collect them, then continue.

## Step 3: Update bigmemory/热区/状态简报.md

Synthesize all information and fully rewrite the state brief:

```markdown
# Project State Brief
> Last updated: [ISO datetime]

## Current Work
- [Extract current active work from experiment ledgers, paper, and survey files]

## Key Context
- [Stable project facts: baseline subproject, current Python module, Lite3 robot, simulation platform, algorithm choice, etc.]
- [Current stage and key technical choices]

## Recent Warnings
- [Risks or blockers to watch]
```

## Step 4: Complete the .pipeline/ Knowledge Base

Check for missing entries and fill them as needed:

| Check Item | File | Action |
|---|---|---|
| New experiment has ledger? | `.pipeline/experiments/` | Create `YYYYMMDD_<topic>.md` if missing |
| New literature is indexed? | `.pipeline/literature/index.md` | Append rows if missing |
| New survey has conclusions? | `.pipeline/survey/` | Create `<topic>.md` if missing |
| New terminology exists? | `.pipeline/terminology/terminology.md` | Append rows if missing |

## Step 5: Confirm Completion

After writing, use `AskUserQuestion`:

> **Sync complete**
>
> Updated:
> - `bigmemory/热区/状态简报.md` - refreshed project state
> - `.pipeline/` - completed missing knowledge-base entries
>
> Next?

Options:
- `Continue current task`
- `View updated progress (/plan)`
- `Nothing else`
