# Trellis 0.6.14 Upgrade Validation

## Outcome

The project-managed Trellis files were upgraded from `0.6.7` to `0.6.14`.
The installed CLI and project version both report `0.6.14`, and the final
`trellis update --dry-run` reports no pending version update.

The updater retained a local recovery snapshot at
`.trellis/.backup-2026-08-13T12-24-26/`.

## Local Customization Decisions

1. `.trellis/config.yaml`
   - Preserved `session_auto_commit: false`.
   - Preserved the six-worker channel limit.
   - Made `codex.dispatch_mode: inline` explicit so the `0.6.14` default of
     native sub-agent dispatch cannot change project behavior.
   - Incorporated the new trusted-context, context-injection-limit, and
     per-turn skip-keyword documentation without enabling new optional values.
2. `AGENTS.md`
   - Accepted the `0.6.14` Trellis-managed block.
   - Verified that all Lite3 project rules outside the managed block remained
     unchanged.
3. `.claude/settings.json`
   - Kept the local file unchanged because the candidate only removed the
     project-owned Git, hot-zone, and reviewed-state hooks and added no required
     `0.6.14` registration.
4. `.codex/hooks.json`
   - Added the `SubagentStart` registration for
     `.codex/hooks/inject-subagent-context.py`.
   - Preserved the root-resolving workflow hook plus project-owned Git,
     hot-zone, and reviewed-state hooks.
5. `.codex/config.toml`
   - Kept the local file unchanged. It already pins `agents.max_depth = 1` and
     additionally preserves the project document-size limit, worker limit, and
     repository-local Git identity policy that the generic candidate omitted.

All five updater-generated `.new` candidates were reviewed and then removed.
They remain reproducible with `trellis update --create-new --migrate`.

## Validation Evidence

The following checks completed with exit status zero:

- `python3 -m compileall -q` across Trellis scripts, Codex/Claude/Cursor hooks,
  and shared skills;
- shell syntax validation for all tracked hook/skill shell scripts;
- JSON, TOML, and YAML parsing (`3` JSON files, `10` TOML files, and the
  Trellis YAML configuration);
- `task.py validate`, `task.py current --json`, and `task.py list --json`;
- package discovery plus phase and session context loading;
- live Codex workflow-state, SessionStart, and SubagentStart hook payloads;
- Git and hot-zone keyword gating, including silence on unrelated prompts;
- the `no-trellis` per-turn skip path;
- Trellis skill-link resolution and shared/Claude/Cursor bundled-skill parity;
- absence of hard-coded sibling `/machine-dog/` paths in migrated Trellis
  skills;
- `trellis mem --help`, `trellis channel --help`, and
  `trellis platforms --json`;
- `codex exec --strict-config --version` (`codex-cli-exec 0.142.3`);
- `git diff --check` using the project harness exclusions;
- final `trellis update --dry-run` at project/CLI/latest version `0.6.14`.

The SubagentStart smoke intentionally used an inline-mode task with empty
`check.jsonl`. Its stderr warning correctly stated that only task artifacts
would be injected; stdout remained valid JSON and included the current task.

## Preservation Evidence

Before and after the update, content hashes matched for all pre-existing
out-of-scope data:

- `.pipeline/literature/index.md`:
  `355363378d2b3cdfbd1c6ac84f969910b04cb4851c7dff97d41f0d6a5e189bcb`;
- `.pipeline/survey/2026-08-12_quadruped_dual_layer_planner_upstream_survey.md`:
  `77ac7254fa459c2732d13831c25da736703c10c35ea3feaa60ae24b12444ae01`;
- aggregate `docs/research/2026-08-04-quadruped-path-planning-intro/` manifest:
  `10cf88abd0223f6aa27b3b0cc831535c9b0c8605ce8d7939ada5ab9a7cb55ab5`;
- aggregate pre-existing `.trellis/tasks/`, `.trellis/spec/`, and
  `.trellis/workspace/` manifest, excluding this maintenance task:
  `609ea9956276bc09dcacfefa630af92c78c884d12a64b81c3a9acfc3ecdab78b`.

The final Git staging gate contained `69` Trellis upgrade, harness-integration,
and maintenance-task files with zero forbidden paths. The existing `.pipeline/`
and `docs/research/` paths remained explicitly excluded.

## Claim Boundary

This evidence validates the local Trellis harness upgrade and its declared
configuration contracts. It does not validate navigation code, SCAN-Planner,
simulation, the 5070 Ti, or any real-robot behavior.

## Specification Review

No `.trellis/spec/` update is required. The existing project harness contract
already defines the executable invariants exercised here: version matching,
disabled automatic commits, managed platform files, hook payload behavior,
dirty-worktree preservation, and the required validation commands. The
release-specific five-file merge record and recovery path are task evidence,
not a new project-wide implementation convention. Leaving the existing spec
tree untouched also satisfies this task's explicit preservation contract.
