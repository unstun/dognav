# Update Trellis to 0.6.14

## Goal

Upgrade the Trellis-managed project files from version `0.6.7` to `0.6.14`
without losing project-specific workflow rules, platform configuration, task
history, specifications, or unrelated user work.

## Background

- The installed `trellis` CLI reports version `0.6.14`.
- The project reports Trellis version `0.6.7` and offers an update to
  `0.6.14`.
- A read-only `trellis update --dry-run` found:
  - one new managed Codex hook,
    `.codex/hooks/inject-subagent-context.py`;
  - upstream template updates to Trellis runtime scripts, workflow text,
    bundled skills, hooks, and Codex agent definitions;
  - five locally customized files requiring an explicit merge decision:
    `.trellis/config.yaml`, `AGENTS.md`, `.claude/settings.json`,
    `.codex/hooks.json`, and `.codex/config.toml`;
  - user data under `.trellis/workspace/`, `.trellis/tasks/`, and
    `.trellis/spec/` classified as preserved;
  - the obsolete `.pi/skills` migration target absent or protected, so it is
    skipped.
- The working tree already contains unrelated survey and CAD/research changes.
  They belong to Dr Sun and are outside this maintenance task.

## Requirements

- R1. Use the installed `0.6.14` CLI; do not modify a global package cache or
  install a different Trellis release.
- R2. Run the update conservatively with migration enabled and `.new` sidecars
  for locally customized managed files. Do not use `--force`.
- R3. Review every generated sidecar against the corresponding local file.
  Preserve project-specific rules and settings, and merge only upstream changes
  required for `0.6.14` compatibility.
- R4. Preserve `.trellis/tasks/`, `.trellis/spec/`, `.trellis/workspace/`, and
  `.trellis/.developer/`, except for the maintenance task files created for
  this work.
- R5. Do not modify, stage, discard, or reformat unrelated survey, literature,
  CAD, or research files already present in the working tree.
- R6. Keep the existing safety choices unless `0.6.14` requires a compatible
  representation, including `session_auto_commit: false` and Codex inline
  execution.
- R7. Review the final task-owned diff for unexpected deletion, migration, or
  cross-platform drift before declaring the upgrade complete.
- R8. Validate Python runtime files, JSON and TOML configuration, task context,
  workflow-state injection, session context, Codex configuration, Trellis
  memory/channel command availability, whitespace, and final update status.
- R9. Do not claim the update complete unless the project version and CLI
  version both report `0.6.14` and the final dry-run reports no pending version
  upgrade.
- R10. Keep commit scope limited to this Trellis maintenance task. Do not stage
  or commit unrelated existing changes.

## Acceptance Criteria

- [x] AC1. `trellis --version` and `.trellis/.version` both report `0.6.14`.
- [x] AC2. The new Codex hook and all unmodified managed template updates from
  the dry-run are present.
- [x] AC3. Each of the five locally customized files has a documented merge
  decision, with project-specific content preserved.
- [x] AC4. Trellis user data directories and the pre-existing unrelated dirty
  paths remain present and unchanged by this task.
- [x] AC5. Python compilation, JSON parsing, TOML parsing, task validation,
  workflow/session hook smoke tests, `trellis mem --help`,
  `trellis channel --help`, Codex strict configuration parsing, and
  `git diff --check` pass.
- [x] AC6. A final `trellis update --dry-run` reports the project up to date or
  otherwise shows no pending `0.6.7` to `0.6.14` upgrade.
- [x] AC7. The reviewed final diff contains only Trellis maintenance files and
  this task's records; no unrelated user changes are staged or committed.

## Out of Scope

- Changing the selected Trellis workflow or Codex dispatch mode.
- Reorganizing or closing existing Trellis tasks.
- Updating project research state, survey documents, CAD artifacts, or hot
  memory.
- Beginning the SCAN-Planner reproduction or using the 5070 Ti.
- Publishing, pushing, or opening a pull request unless Dr Sun separately asks.
