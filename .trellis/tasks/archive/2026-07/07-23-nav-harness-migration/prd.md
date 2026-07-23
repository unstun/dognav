# Migrate research harness into navigation project

## Goal

Migrate current reusable AGENTS, Trellis, Codex, Claude, Cursor, pipeline, memory, and project skills without copying machine-dog experiment history.

## Requirements

- Treat `/Users/sun/tongbu/study/phdproject/machine-dog-nav` as the only
  source of truth for navigation code and project state.
- Preserve the repository's existing tracked files, Matt Pocock skill setup,
  and untracked `docs/research/` material.
- Install the same local Trellis release used by `machine-dog` and enable its
  Codex, Claude Code, and Cursor adapters.
- Adapt the reusable human-review, evidence, git, memory, research, and
  source-sync rules from `machine-dog`; do not copy locomotion-specific
  experiment labels or active-task state.
- Create fresh `.pipeline/` and `bigmemory/` structures for navigation.
- Migrate a small, reviewable set of reusable project skills needed for
  repository survey, literature work, diagnosis, review, project status, and
  memory retrieval.
- Disable automatic git commits. Every commit must be made after validation
  with an explicit task-owned path list.
- Keep `docs/research/` out of this task's commit.

## Constraints

- Do not copy `.trellis/tasks/`, `.trellis/workspace/`, `.pipeline/experiments/`,
  or `bigmemory/` records from `machine-dog`.
- Do not restore the pre-reset Research Contract or pre-edit auto-backup hook.
- Do not overwrite third-party skill symlinks already present in
  `.agents/skills/` and `.claude/skills/`.
- Do not add navigation implementation, simulator code, or experiment results.

## Acceptance Criteria

- [x] `AGENTS.md` is the navigation repository's behavior source of truth and
      `CLAUDE.md` remains a thin wrapper.
- [x] `trellis --version` and `.trellis/.version` agree; task creation,
      validation, and context discovery work locally.
- [x] Codex, Claude Code, and Cursor configuration files parse and their hook
      entry points pass syntax checks.
- [x] Fresh `.pipeline/` and `bigmemory/` indexes clearly state that no
      navigation implementation or runtime evidence exists yet.
- [x] Migrated skills are tracked, discoverable, and contain no hard-coded
      `machine-dog` repository path.
- [x] The staged diff contains only harness migration paths and excludes
      `docs/research/`.

## Notes

- Source harness: `/Users/sun/tongbu/study/phdproject/machine-dog`.
- Target repository: `/Users/sun/tongbu/study/phdproject/machine-dog-nav`.
