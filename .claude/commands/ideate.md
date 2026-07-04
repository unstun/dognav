---
description: Generate and evaluate research ideas, showing intermediate results at each step for user decisions.
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**

You are the Lite3 quadruped navigation DRL Conductor. Research idea generation and final selection both require user participation.

## Step 1: Confirm Prerequisites

```text
bigmemory/热区/状态简报.md
.pipeline/literature/index.md           # Existing literature.
.pipeline/survey/                       # Existing survey conclusions.
.pipeline/terminology/terminology.md
```

Use `AskUserQuestion` to show the current literature base:

> There are X existing papers, and survey conclusions cover these topics:
> [list files under .pipeline/survey/]
>
> Ready to generate research directions from the literature and survey conclusions.

Options:
- `Confirm, start generation`
- `Show existing survey conclusions first`
- `Develop one specified direction`

## Step 2: Generate Ideas

Call the `inno-idea-generation` skill and generate 5 candidate research directions based on `.pipeline/literature/index.md` and survey conclusions under `.pipeline/survey/`.

## Step 3: Show 5 Ideas and Wait for User Filtering

Use `AskUserQuestion`:

> The following 5 research directions were generated:
> 1. [Idea A]: ...
> 2. [Idea B]: ...
> ...
>
> Next, evaluate novelty and feasibility for these directions.

Options:
- `Evaluate all`
- `Evaluate only the ones I am interested in (I will specify which)`
- `These directions are wrong; regenerate`

## Step 4: Evaluate and Score

Call the `inno-idea-eval` skill to score selected ideas on novelty / feasibility / impact, each from 1 to 5.

## Step 5: Final Decision

Show scoring results with `AskUserQuestion`:

> Evaluation results:
> - [Idea A]: novelty 4 / feasibility 3 / impact 5
> - [Idea B]: novelty 5 / feasibility 2 / impact 4
> - ...
>
> Which direction do you prefer?

List each idea name as an option, plus `I will describe my own idea`.

After the user selects, update `bigmemory/热区/状态简报.md` and `bigmemory/热区/未关闭决策.md` with the chosen direction and rejected directions.

## Reminders

- **Multi-model divergence**: when feasible, ask Gemini with large context and Codex with independent knowledge to generate ideas separately, then let Claude merge and deduplicate. Different models have different blind spots, and ensemble can surface useful angles.
- **Limit adversarial review rounds**: idea review should usually stop after at most 3 rounds, then Dr Sun decides. Avoid review loops without terminal conditions. See `.claude/rules/gotchas.md`.
- **Context before divergence**: idea quality depends on survey depth in `.pipeline/survey/`. If survey context is shallow, ideation quality will be limited.
