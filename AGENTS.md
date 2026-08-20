# Lite3 Autonomous Navigation Research Project

> Scope: `/Users/sun/tongbu/study/phdproject/machine-dog-nav/**`.
> Source of truth: this file (`AGENTS.md`). `CLAUDE.md` imports it through
> `@AGENTS.md`.

## Project Purpose

This repository develops autonomous navigation above the Lite3 locomotion
controller maintained in the sibling `machine-dog` repository. The immediate
direction is to study and reuse open-source systems, beginning with the
geometric-waypoint-to-locomotion loop. That starting point is not a permanent
scope ceiling: perception, mapping, obstacle avoidance, terrain-aware planning,
VLA, simulation, and real-robot integration may be added when evidence supports
them.

The two repositories have different responsibilities:

- `machine-dog`: locomotion training, evaluation, and deployment.
- `machine-dog-nav`: navigation research, upstream acquisition, integration,
  evaluation, and navigation-to-locomotion interface work.

## Identity And Protocol

This is a long-horizon PhD research project.

1. Every reply to Dr Sun starts with `Dr Sun,`.
2. Use Chinese for interaction with Dr Sun unless he requests another language.
   Use clear professional English for code, configuration, and repository-facing
   technical documentation unless the requested artifact is Chinese.
3. At the start of a session, identify the current stage:
   **planning -> experiment + analysis -> writing**. Do not silently mix stages.
4. Human review comes before speed. If requirements have several materially
   different interpretations, explain the difference and ask before choosing.

## Research Discipline

1. AI output is untrusted until verified. Search results and prior AI summaries
   are leads, not evidence.
2. Read local sources first. For professional claims, verify primary papers,
   official documentation, or the upstream repository itself and cite a short
   file reference or URL.
3. Separate these labels:
   - `surveyed`: papers or repositories were inspected.
   - `reproduced`: an upstream run was executed with recorded evidence.
   - `integrated`: upstream behavior works inside this repository.
   - `validated`: the declared acceptance test passed.
   Never promote one label into another.
4. Prefer an existing open-source implementation over writing a new framework
   from scratch, but record its URL, license, pinned commit, dependencies,
   original run instructions, and local modifications.
5. Keep third-party source inside this project under a dated, purpose-named
   directory. Do not use `/tmp` as durable storage.
6. `.pipeline/terminology/terminology.md` is the terminology source of truth.
   Check it before introducing project terms in research or design documents.

## Source Of Truth And Sync Gate

The local `machine-dog-nav` repository is the only source of truth for
navigation code and project state.

- Upstream repositories are read-only references until deliberately imported.
- Remote machines and simulator workspaces are execution copies only.
- Temporary remote diagnostic edits are allowed, but final changes must return
  to the same local paths and be visible in local `git diff`.
- A remote-only success is not reproducible evidence.
- Navigation-to-locomotion integration must pin the sibling `machine-dog`
  interface version or commit instead of copying an unidentified policy.

## Engineering Rules

1. Think before editing. Convert requests into checkable goals and state a short
   plan for non-trivial work.
2. Keep scope small. Do not refactor or reformat unrelated files.
3. Preserve user changes in a dirty worktree. Stage only paths owned by the
   current task.
4. Automatic pre-edit or session commits are forbidden. Commit only after a
   meaningful change is verified and the staged diff is reviewed.
5. Do not claim `fixed`, `working`, `reproduced`, or `complete` without a direct
   test, build, simulator run, or equivalent runtime check.
6. Formal training, long remote runs, destructive data operations, and
   real-robot actuation require explicit authorization from Dr Sun.
7. For external execution packages, state:
   - local source of truth;
   - exact sync gate;
   - expected artifacts;
   - claim boundary if the run is incomplete.
8. Store research PDFs, source snapshots, run logs, configurations, models, and
   evaluation artifacts inside the project using date/topic/purpose paths.

## Project State Layout

- `.trellis/`: tasks, workflow, specifications, and session journals.
- `.pipeline/`: reviewed research indexes, terminology, surveys, experiment
  records, templates, and external task packages.
- `bigmemory/热区/`: current status, recent changes, and open decisions.
- `bigmemory/冷区/`: durable change, pitfall, research, rationale, and milestone
  records.
- `docs/research/`: human-readable research documents.

Existing repository conventions remain active:

- Issues and PRDs live as GitHub issues, managed with `gh`. See
  `docs/agents/issue-tracker.md`.
- Default triage labels are `needs-triage`, `needs-info`, `ready-for-agent`,
  `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.
- Multi-context domain documentation follows `docs/agents/domain.md`.

## Current Boundary

As of 2026-08-19, the repository has a project-integrated Foxy SCAN-Planner to
Lite3 V12 Isaac closed loop. Immutable Office L0 candidates 38 and 39 passed
their declared automated AC54 gate under their original inputs. The current
MID-360 working revision is `office-r2.0.0-preflight`, and its golden
third-person plus same-run native-RViz dual-view result is only a 10.04-second
human-review preflight. It has not rerun full AC54, AC55 remains pending Dr
Sun, and both `accepted_revision` and `formal_candidate` remain null. This is
not an upstream SCAN reproduction, real-robot validation, or completed Office
navigation task.

<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

If you're using Codex or another agent-capable tool, additional project-scoped helpers may live in:
- `.agents/skills/` — reusable Trellis skills
- `.codex/agents/` — optional custom subagents

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

<!-- TRELLIS:END -->
