# Trellis 0.6.14 Upgrade Plan

## Preparation

- [x] Record the scoped pre-update Git status, project version, CLI version,
  current task, and dry-run result.
- [x] Confirm that Trellis-managed tracked files are clean apart from this
  maintenance task and list unrelated dirty paths for exclusion.

## Upgrade

- [x] Run `trellis update --create-new --migrate`; never use `--force`.
- [x] Confirm that user-data directories were preserved and inspect every
  migration result.
- [x] Review all generated `.new` files and record one merge decision per local
  customization.
- [x] Apply only the compatibility changes needed by `0.6.14`, preserving the
  repository's existing workflow and safety settings.
- [x] Remove only the reviewed, updater-generated `.new` sidecars.

## Validation

- [x] Confirm `.trellis/.version` and `trellis --version` are both `0.6.14`.
- [x] Compile Trellis and platform Python hooks with `python3 -m compileall`.
- [x] Parse managed JSON and TOML configuration files.
- [x] Run `task.py current`, `task.py validate`, and compact context loading.
- [x] Smoke-test session-start and workflow-state injection for the current
  Codex session and verify inline mode is still emitted.
- [x] Run `trellis mem --help` and `trellis channel --help`.
- [x] Run `codex exec --strict-config --version`.
- [x] Run `git diff --check` and review the complete task-owned diff.
- [x] Re-run `trellis update --dry-run` and confirm no version update remains.
- [x] Verify unrelated dirty paths are byte-for-byte unchanged relative to the
  recorded pre-update state.

## Finish

- [x] Record validation evidence and the five local-customization decisions in
  the task.
- [x] Run the Trellis quality gate and update project specs only if the upgrade
  reveals a durable project-specific contract not already documented.
- [x] Stage only Trellis maintenance paths, review the staged diff, commit the
  verified upgrade, and archive the task according to the project workflow.
