---
name: agent-deliberation
description: Use when Dr Sun asks for multi-agent discussion, cross-review, independent opinions, or agent debate before changing machine-dog-nav experiments, code, or paper claims.
---

# Agent Deliberation

Use this skill to run a small expert panel around one question. It is for thinking before action, not for replacing machine-dog-nav research rules.

## When To Use

Use when Dr Sun asks for:

- multi-agent discussion around the same question
- cross-review, independent opinions, or a counterargument
- small-panel review of experiment design, code plans, or paper claims
- separate agent opinions before a change

Do not use for simple single-file edits, routine command output, or questions that one local inspection can answer.

## Roles

The main session is `Host`.

Spawn agents only when current platform rules and Dr Sun's instruction allow agent delegation. Spawn only the roles needed for the question:

- `Proposer`: proposes a plan, hypothesis, or implementation direction.
- `Critic`: checks missing evidence, weak assumptions, experiment boundary, and verification gaps.
- `Evidence Checker`: separates verified project evidence from AI-only guesses.
- `Recorder`: optional; compresses the discussion into consensus, disagreement, and items needing Dr Sun confirmation.

Keep the panel small. Default to `Proposer`, `Critic`, and `Evidence Checker`.

## Required Output From Each Agent

Each agent must answer in this format:

```text
claim: <main view>
basis: <file path with line, experiment id plus artifact/metric location, DOI/URL/PDF, exact command output, or "ai_only">
uncertainty: <what is still not confirmed>
suggestion: <next action or check>
```

If the source is not directly checkable, the agent must write `basis: ai_only`.

## Host Duties

Before spawning agents:

1. State the single question being discussed.
2. Provide only the necessary context and source hints.
3. Tell subagents not to edit files.

After agents respond:

1. Merge repeated points.
2. Separate the result into:
   - consensus
   - disagreement
   - items needing Dr Sun confirmation
3. Mark any `ai_only` item as unverified.
4. Do not treat discussion output as experiment evidence.

## Machine-Dog Boundaries

This skill does not replace:

- Research Contract for experiment admission and success/failure signals.
- `.pipeline/experiments/` for experiment records.
- `0_trials/` for exploratory scripts and one-off visualizations.
- `bigmemory/` for long-term project memory.
- source verification for paper facts and citations.

Default behavior is conversation-only. If the discussion produces a durable preference, workflow rule, mistake record, or project decision, list it as `pending archive` and let the archive process or Dr Sun handle long-term memory.

Do not create `docs/agents/`, `CONTEXT.md`, `docs/adr/`, or new `.pipeline` structures unless Dr Sun explicitly asks for that infrastructure.
