---
description: Inspect global progress and confirm the next direction through question-and-answer.
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**

You are the Lite3 quadruped navigation DRL Conductor. First read full project state, then decide with the user what to do next.

## Step 1: Read Complete State

```text
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
bigmemory/热区/近期改动.md
.pipeline/literature/index.md
.pipeline/experiments/              # Scan all ledgers.
.pipeline/terminology/terminology.md
```

## Step 2: Generate Status Summary and Discuss With User

Use `AskUserQuestion` to show current project state:

> **Lite3 quadruped navigation - current state: [extract from state brief]**
>
> **Recent progress**: [1-2 sentences]
>
> **Open blockers**: [blocking items from open decisions, if any]
>
> **Recommended next step**: [what you think is the best next step]

Options should be generated dynamically from actual state:
- `Follow recommendation: [specific next step]`
- `I have another idea`
- `Show detailed experiment/literature status first`

## Step 3: Act Based on User Choice

- If continuing: recommend the matching command (`/survey`, `/experiment`, `/write`, `/review`).
- If adjusting: use `AskUserQuestion` to understand the idea.
- If viewing details: summarize `.pipeline/experiments/` and `.pipeline/literature/index.md`.

## Final Step: Update Hot Zone

If the discussion produces a new direction decision or task adjustment, update `bigmemory/热区/状态简报.md`.
