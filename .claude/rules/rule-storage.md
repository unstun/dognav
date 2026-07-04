---
paths: ["CLAUDE.md", "AGENTS.md", ".claude/rules/**"]
---
# Behavior Rule Storage Location

Feedback, preferences, and behavior norms should be stored in `CLAUDE.md` or `.claude/rules/*.md`, which are version-controlled and visible to the project.
Do not store them under private `~/.claude/projects/` paths, which Dr Sun cannot see and which are not version-controlled.
For longer text, use `.claude/rules/<topic>.md` plus a one-line index in `CLAUDE.md` or this file.
