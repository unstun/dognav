---
description: Peer review: review 3_paper/main.tex and discuss fixes item by item.
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**

You are the Lite3 quadruped navigation DRL Reviewer. Paper review results need to be analyzed with the user.

## Step 1: Confirm Review Scope

```text
3_paper/main.tex                         # Paper body.
3_paper/references.bib                   # References.
.pipeline/experiments/                   # Experiment ledgers for data consistency.
.pipeline/terminology/terminology.md     # Terminology rules.
bigmemory/热区/状态简报.md               # Project context and stated contributions.
```

Use `AskUserQuestion`:

> **Ready to peer-review:**
> - `3_paper/main.tex` (single-file paper)
>
> **Review dimensions**: technical contribution / experiment sufficiency / writing quality / citation accuracy / data consistency / terminology consistency
>
> Follow review standards in `.claude/agents/reviewer.md`.

Options:
- `Start review`
- `Add special focus`
- `Cancel`

If the user has extra focus points, record them and include them in review.

## Step 2: Execute Review

Use the `inno-paper-reviewer` skill and review the 6 dimensions defined in `.claude/agents/reviewer.md`.

Check:
- Whether every `\cite{}` key exists in `references.bib`.
- Whether experiment data in the paper matches ledgers under `.pipeline/experiments/`.
- Whether terminology follows `.pipeline/terminology/terminology.md`.

## Step 3: Discuss Review Results Item by Item

Do not jump directly to a final conclusion. Discuss each item with the user:

> **Review result (technical contribution: X/5)**
>
> Must fix:
> 1. [Issue A] - what do you think?

Use `AskUserQuestion`:
- `Agree, edit`
- `I disagree`
- `This issue is not important; skip`

After each major issue is confirmed by the user, then make batch edits.

## Step 4: Decide Final Conclusion

After all issues are discussed, ask:

> **Your judgment:**

Options:
- `Good enough; paper is basically final`
- `Still needs edits; I will describe where`
- `Needs major revision; return to /write`
