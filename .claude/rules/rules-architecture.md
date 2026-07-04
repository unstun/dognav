---
paths:
  - ".claude/rules/**"
  - "CLAUDE.md"
  - "AGENTS.md"
---
# CLAUDE.md Maintenance Rules

## Injection Mechanism

- `CLAUDE.md` is injected as a user message, not a system prompt, and Claude judges relevance rule by rule.
- `.claude/rules/*.md` without `paths` is fully loaded every session; with `paths`, it is injected only when matching files are read.
- Instruction budget is about 150-200 rules; the root file target is <=100 lines.

## Writing Principles

- **Positive framing over negative framing**: MUST is better than NEVER. Keep NEVER below 10%.
- **Add Why**: reasons help AI handle boundary cases.
- **IMPORTANT/YOU MUST works but is diluted by overuse**: reserve it for truly critical rules.
- **U-shaped bias**: place the most important rules at the beginning and end.

## Content Selection

**Effective content to keep**:
- Non-obvious tool decisions.
- Unusual configuration and project-specific constraints.
- Rules AI repeatedly violates.

**Ineffective content to delete or move out**:
- Directory structure or architecture overviews that agents can discover.
- Narrative background paragraphs.
- Stale structure descriptions.
- Code-style rules executable by linters.

## Advisory vs Deterministic

- `CLAUDE.md` is advisory; hooks are deterministic.
- Mechanical rules that require zero exceptions should become hooks.
