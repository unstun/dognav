# Codex Main-Entry Adapter

This directory is the project-level harness entry for Codex CLI and Codex App. `AGENTS.md` is the cross-CLI source of truth for rules.

## Current Repository Boundary

- project root: `/Users/sun/tongbu/study/phdproject/machine-dog-nav`
- project topic: Lite3 quadruped navigation DRL
- source of truth: local repo
- walking base repo: `/Users/sun/tongbu/study/phdproject/machine-dog`

## Project-Level Configuration

`.codex/config.toml` contains only shared project configuration:

- `project_doc_max_bytes = 65536`
- hooks enabled
- subagent/thread depth limits
- Codex git author

Models, MCP, plugins, sandbox, and approval settings should remain in user-level configuration or launch arguments by default.

## Hooks

`.codex/hooks.json` inherits hooks available to this project:

- `UserPromptSubmit`: inject git state and hot-zone freshness; if `.trellis/` does not exist, the Trellis breadcrumb hook exits silently.
- `PreToolUse`: create a git auto-backup before file edits.
- `PostToolUse`: after trusted-knowledge Markdown edits, reset `reviewed: true` to `reviewed: false`.

## Skills

The Codex skills entry is `.agents/skills/`. These skills were migrated from the walking base repository; before future use, check whether they still contain old experiment paths or old evidence claims.

## Suggested Checks

```bash
git status --short
bash .claude/scripts/sync-harness.sh --check
python3 -m json.tool .codex/hooks.json >/dev/null
```
