---
paths: ["bigmemory/**", ".claude/skills/archive/**"]
---
# Archive Agent Model Constraint

All `/archive` agent calls must explicitly specify a cheap model:
- Claude Code environment: `model: "sonnet"`
- Droid environment: `gpt-5.4-mini`

Do not use Opus for this. Why: archiving is mechanical writing (read template -> write to template -> deduplicate), does not require strong reasoning, and using Opus for 5 parallel workers is expensive with no quality gain.
