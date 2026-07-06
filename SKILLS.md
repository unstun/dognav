# Matt Pocock's Skills — installed here

The 20 curated ("promoted") skills from
[mattpocock/skills](https://github.com/mattpocock/skills) are wired into this
project for **both** coding agents:

| Agent       | Discovery path    | How                                            |
| ----------- | ----------------- | ---------------------------------------------- |
| Claude Code | `.claude/skills/` | project-level skills                           |
| Codex       | `.agents/skills/` | Agent-Skills standard (scanned from repo root) |

Both folders contain relative **symlinks** into a live clone of the upstream
repo at `.skills-upstream/` (git-ignored). Same `SKILL.md` format works for both
harnesses, so one set of files serves both.

## Updating (author-driven — you don't maintain anything)

```bash
git -C .skills-upstream pull   # pull the author's latest
./sync-skills.sh               # re-link (also picks up any newly promoted skills)
```

Restart Codex afterwards so it re-scans skills. Claude Code picks them up on the
next session.

## Using them

- Type `/<skill-name>` in either agent, e.g. `/grill-me`, `/tdd`, `/triage`.
- Run `/ask-matt` — it's the router that maps which skill fits your situation.
- Run `/setup-matt-pocock-skills` once to configure the issue tracker, triage
  labels, and docs location the skills use.

## Notes / caveats

- **`code-review`.** Claude Code ships a built-in `/code-review`, and a project
  skill of the same name would *fully shadow* it. So `sync-skills.sh` excludes
  `code-review` from `.claude/skills/` (via `CLAUDE_EXCLUDE`) — Claude Code keeps
  its built-in `/code-review`, while Codex keeps Matt's `/code-review`. To change
  this, edit `CLAUDE_EXCLUDE` in `sync-skills.sh` and re-run it.
- **User-invoked skills.** Skills with `disable-model-invocation: true`
  (e.g. `grill-me`) are human-only in Claude Code. Codex doesn't honor that flag,
  so the model there may also trigger them. Harmless, just a behavior difference.
- **Fresh clones of this project** won't have `.skills-upstream/` (it's
  git-ignored), so the symlinks would dangle. Re-clone upstream and re-run
  `./sync-skills.sh` to restore them.
