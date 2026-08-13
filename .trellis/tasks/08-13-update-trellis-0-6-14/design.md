# Trellis 0.6.14 Upgrade Design

## Boundary

The upgrade changes only Trellis-managed runtime, workflow, platform-integration,
and bundled-skill files plus the current maintenance task. Project research,
CAD, experiment, specification, task-history, and workspace-journal content are
not migration inputs.

## Upgrade Strategy

1. Treat the installed `0.6.14` CLI as the template source and the current
   project files as the source of truth for local customization.
2. Apply upstream-managed changes with `trellis update --create-new --migrate`.
   Unmodified templates may update automatically; locally customized files must
   be emitted as `.new` candidates rather than overwritten.
3. Compare each candidate with its local counterpart and merge narrowly:
   - `.trellis/config.yaml`: preserve disabled session auto-commit, worker
     limits, and inline Codex behavior while accepting compatible new settings.
   - `AGENTS.md`: preserve all Lite3 research rules and only reconcile the
     Trellis-managed block if required.
   - `.claude/settings.json`: preserve user hooks, permissions, and local tool
     configuration while adding required Trellis hook changes.
   - `.codex/hooks.json`: preserve existing registrations and incorporate only
     required `0.6.14` hook wiring.
   - `.codex/config.toml`: preserve project configuration and inline execution
     while accepting required schema-compatible additions.
4. Remove reviewed temporary `.new` candidates after their decisions are
   reflected in the real files. They can be regenerated with the same update
   command if later review is needed.

## Compatibility Contracts

- The version contract is `.trellis/.version == trellis --version == 0.6.14`.
- The workflow contract is that session-start and workflow-state injection
  still identify the current task and Codex inline mode.
- The data-preservation contract is no content change under existing task,
  spec, workspace, or developer directories, apart from this new task.
- The Git contract is that unrelated dirty paths remain outside the task-owned
  diff and are never staged.

## Failure Handling And Rollback

- Stop before merging if the updater attempts to overwrite a locally modified
  file instead of creating a sidecar.
- Stop and inspect any migration that deletes a present project-owned path.
- If a validation fails, change one compatibility issue at a time and rerun the
  targeted check before the full gate.
- Do not use `git reset`, `git checkout`, or broad file restoration. Because
  pre-existing user work is present, rollback is limited to task-owned paths
  identified from the before/after scoped diff.
- If `0.6.14` cannot satisfy the existing workflow contracts, leave the task in
  progress with the exact failing evidence rather than declaring success.

## Claim Boundary

Passing this task proves that the local project harness is upgraded and its
declared configuration checks pass. It does not validate research code,
simulation, remote execution, or existing task correctness.
