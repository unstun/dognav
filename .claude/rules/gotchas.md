# Gotchas

## AI Usage Gotchas

- Do not mix WebFetch and WebSearch in the same parallel batch. A WebFetch 403 can cascade and degrade same-batch WebSearch calls. Use at most 2 same-type calls per parallel batch.
- PDF links often fail to parse. Prefer HTML versions such as `arxiv.org/html/`.
- Subagent prompts must force WebFetch/Grep against real sources before answering and must include URLs plus original snippets. LLMs can still fabricate "original quotes"; the main session must spot-check quote fields.

## Context Management Gotchas

- Feeding long paper PDFs directly into context dilutes attention. Prefer arXiv LaTeX source or HTML versions, and read only relevant sections as needed.
- High-noise content such as install errors, download logs, and training logs lowers all later reasoning quality once it enters the main session context. Isolate it with subagents.
- Discussing multiple ideas in one context causes interference; AI will drift toward prior ideas without noticing.

## Multi-Model Collaboration Gotchas

- Two models reviewing each other can always find "more improvements". A review loop without a terminal condition is a false requirement. One role must make the final decision.
- After experiment results arrive, AI will rationalize any number. Research Contract is the only countermeasure.
- In Claude Code/Droid, Codex uses slash commands (`/codex:review`, `/codex:rescue`, `/codex:adversarial-review`) or Agent (`codex:codex-rescue`) and disables `mcp__codex__*`, which was removed from `~/Library/Application Support/Claude/claude_desktop_config.json`. Cursor is an exception: do not use the Codex plugin/Task path. The main session only generates manual task packages for Dr Sun to input into Codex. Why: the TypeScript MCP SDK hard-codes a 60s request timeout, and the Cursor plugin path consumes main-session orchestration tokens while sandbox and main shell differ.
