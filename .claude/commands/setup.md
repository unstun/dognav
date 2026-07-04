---
description: Initialize the research harness structure (bigmemory/ + .pipeline/ + .claude/).
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**

You are initializing the Lite3 quadruped navigation DRL research harness for the current directory.

## Step 1: Check Existing Structure

```bash
ls -la bigmemory/ .pipeline/ .claude/ 2>/dev/null || echo "some directories are missing"
```

Use `AskUserQuestion` to report:

> **Environment check**:
> - bigmemory/: [exists / missing]
> - .pipeline/: [exists / missing]
> - .claude/: [exists / missing]

Options:
- `Initialize missing directories`
- `Reinitialize everything (overwrites existing files)`
- `Cancel`

## Step 2: Create Directory Structure

```bash
# bigmemory - session memory (hot zone / cold zone)
mkdir -p bigmemory/热区
mkdir -p bigmemory/冷区/{改动记录,踩坑记录,调研记录,心路历程,里程碑}
touch bigmemory/冷区/{改动记录,踩坑记录,调研记录,心路历程,里程碑}/.gitkeep

# .pipeline - project knowledge base (flat-file database)
mkdir -p .pipeline/{terminology,literature,survey,experiments}

# .claude - agent configuration
mkdir -p .claude/{agents,commands,rules,scripts,skills}
```

## Step 3: Write Initial Files, Skipping Existing Ones

**bigmemory/热区/状态简报.md**:

```markdown
# Project State Brief
> Last updated: [ISO datetime]

## Current Work
- [To fill]

## Key Context
- Experiment code: declare a Python module by nav baseline subproject; default directory is `2_experiment/nav_baselines/<topic>/`.
- Robot: DeepRobotics Lite3 quadruped robot (12 DOF).
- Simulation: Isaac Lab / MuJoCo.
- Algorithms: PPO / SAC for continuous action spaces.
- Task: quadruped navigation; the specific task must be defined by Research Contract.

## Recent Warnings
- None.
```

Create blank templates for **bigmemory/热区/未关闭决策.md** and **bigmemory/热区/近期改动.md**.

Generate **bigmemory/格式规范.md** from template, covering hot-zone capacity budget and cold-zone format.

Write **.pipeline/README.md** as the knowledge-base guide.

Create initial blank versions for **.pipeline/terminology/terminology.md**, **.pipeline/literature/index.md**, and each library **README.md**.

## Step 4: Verify Harness Completeness

```bash
bash .claude/scripts/sync-harness.sh
```

## Step 5: Completion Confirmation

Use `AskUserQuestion`:

> Harness initialization complete.
>
> Structure:
> - `bigmemory/` - session memory (hot zone + cold zone)
> - `.pipeline/` - project knowledge base (terminology/literature/survey/experiments)
> - `.claude/` - agent configuration (agents/commands/rules/scripts/skills)
>
> Next:
> - Run `/plan` to inspect global state
> - Or start work directly

Options:
- `Start; run /plan`
- `I will inspect the file structure first`
