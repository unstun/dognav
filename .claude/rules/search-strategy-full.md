---
paths: [".pipeline/survey/**", ".pipeline/literature/**", "1_survey/**", "**/*literature*", "**/*survey*"]
---
# ============================================================
# Web Search Strategy (Full)
# Hard Rule #12 Detailed Decision Framework
# ============================================================

Core principle: **default to web access when needed, and prioritize information quality**. Control context growth by isolating work in agents, not by limiting search count.

## Decision Flow

```text
Query arrives
  |
  |-- Existing project information?
  |     -> Auggie MCP semantic retrieval
  |        -> If Auggie MCP errors, fall back to Grep + Glob
  |
  |-- Quick verification (1-2 facts or concept checks)
  |     -> Grok Search MCP direct call; lightweight result enters Opus context
  |        -> Precise question: enable_planning=false
  |        -> Complex question: enable_planning=true
  |
  |-- Deep research (multi-step / multi-source / technical choice / literature search)
  |     -> spawn Search Agent (model=sonnet)
  |        -> multiple rounds of WebSearch + WebFetch + Grok Search
  |        -> return <=800-character summary + source URLs
  |        -> Opus context receives only the summary
  |
  |-- Paywall / tool-limited page (WebFetch 403, login required, etc.)
  |     -> list retrieval items for Dr Sun to handle in Super Grok web UI
  |        -> AI continues after Dr Sun returns results
  |        -> Why: Super Grok is already subscribed, has zero token cost here, and may be higher quality
  |
  |-- Framework/library docs
  |     -> context7 MCP, more precise than general search
  |
  `-- Page requiring JS rendering
        -> Playwright MCP as a last resort
```

## Available Tools

| Tool | Type | Use Case | Context Impact |
|---|---|---|---|
| Auggie MCP (`mcp__auggie.codebase_retrieval`) | MCP | Project semantic search; current Codex server is `auggie`, actual transport follows `codex mcp get auggie`; `codebase-retrieval` is only capability name or legacy spelling | Depends on Auggie index |
| Grok Search (`web_search`) | MCP | Quick verification and synthesized answer | Lightweight direct call |
| Grok Search (`get_sources`) | MCP | Verify source URL quality | Very light |
| WebSearch | built-in | Broad search for links | Medium |
| WebFetch | built-in | Read a specific URL precisely | Controlled by prompt precision |
| context7 (`resolve-library-id` / `query-docs`) | MCP | Official framework/library docs | Light |
| Playwright | MCP | JS-rendered pages | Very heavy; last resort |

## Grok Search MCP Usage

- Precise question: `enable_planning=false` for quick return.
- Complex/multifaceted question: `enable_planning=true` for automatic 6-stage planning.
- The `platform` parameter can cause timeouts when over-constrained; avoid it unless necessary.
- After search, call `get_sources` if source URL quality needs validation.

## Search Agent Rules

**All web search agents use `model: "sonnet"`**. Do not use Opus.
Why: search is IO-bound, waiting on network and parsing pages. It does not need Opus-level reasoning; Sonnet is enough and cheaper, and isolation protects the main context.

For deep research, spawn a Sonnet subagent using skill `web-search`:

- Agent chooses the best combination of WebSearch / WebFetch / Grok Search.
- Output <=800-character summary + source URL list.
- Quotes/data must come from WebFetch original text or Grok returned content. LLM fabrication is forbidden.
- Internal WebFetch calls <=5 to control subagent context.
- If blocked, report a list of unresolved items for Dr Sun or the main AI to decide.

## Anti-Bloat Mechanism

- **Quick path**: Grok direct results are lightweight enough for Opus context.
- **Deep path**: Search Agent isolates work; main context receives only compact summary.
- **WebFetch prompt must be precise**: vague prompts pour full pages into context; precise prompts are manual dynamic filtering.
- **Do not mix WebFetch and WebSearch in one parallel batch**: WebFetch 403 can degrade same-batch WebSearch calls.

## Forbidden

- Do not answer professional questions from AI training memory alone (hard rule #8).
- Do not use Playwright for paywalled literature; token cost is too high.
- PDF links often fail to parse. Prefer HTML versions such as `arxiv.org/html/`.
