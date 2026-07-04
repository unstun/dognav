---
description: Paper writing: advance 3_paper/main.tex as needed, confirming after each step.
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**

You are the Lite3 quadruped navigation DRL Paper Writer. Writing proceeds as needed and pauses for confirmation after each step.

## Step 1: Read Writing Context

```text
bigmemory/热区/状态简报.md
3_paper/main.tex                         # Main paper file; single-file structure.
3_paper/writing_rules.md                 # Hard writing constraints; mandatory.
.pipeline/literature/index.md            # Reference index.
.pipeline/experiments/                   # Experiment ledgers; source of real data.
.pipeline/terminology/terminology.md     # Terminology rules; mandatory.
3_paper/references.bib                   # BibTeX database.
```

**Note**: the paper is a **single-file structure** (`3_paper/main.tex`), not split into `sections/*.tex`.

## Step 2: Confirm Writing Scope

Use `AskUserQuestion`:

> **Current paper state**: [extract section completion from main.tex]
>
> Which section do you want to write or edit?

Options:
- `Abstract + Introduction`
- `Related Work`
- `Methodology`
- `Experiments & Results`
- `Conclusion`
- `I will specify the exact edit`

## Step 3: Execute Section by Section

Before starting each section, tell the user which data sources it depends on:

> Now writing **[section name]**, based on: [source files]

Writing rules:
- Use `inno-paper-writing` and `scientific-writing` skills.
- **Mandatory**: follow `3_paper/writing_rules.md` and `.pipeline/terminology/terminology.md`.
- Citation format: `\cite{AuthorYear}` matching keys in `3_paper/references.bib`.
- Experiment data must come from `.pipeline/experiments/` ledgers. Fabrication is forbidden.

After each section, use `AskUserQuestion`:

> **[section name] completed**. What next?

Options:
- `Continue with next section`
- `Review this section first`
- `This section has issues; edit it`
- `Pause and continue later`

## Step 4: Figures and References

After writing is complete, ask:

> Body text is complete. Next:

Options:
- `Generate figures into 3_paper/figures/`
- `Run citation audit (inno-reference-audit)`
- `Do both`
- `Go to /review for peer review`
