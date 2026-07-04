# ============================================================
# Web Search Strategy (Resident Summary)
# Full rules: .claude/rules/search-strategy-full.md
# ============================================================

Hard rule #12 execution path, from highest to lowest priority:

1. **Inside project**: Auggie MCP semantic retrieval -> Grep + Glob fallback on error.
2. **Quick verification** (1-2 facts): Grok Search MCP direct call, `enable_planning=false`.
3. **Complex question**: Grok Search MCP, `enable_planning=true`.
4. **Deep research** (multi-step / literature / technical choice): spawn Search Agent (`model: sonnet`), return <=800-character summary + source URLs, and keep only the summary in main context.
5. **Paywall/403**: list items for Dr Sun to handle with Super Grok.
6. **Framework/library docs**: context7 MCP.
7. **JS-rendered page**: Playwright as last resort.

Isolation principle: deep research must go through a subagent. Do not run high-noise search inside the main session.

See `.claude/rules/search-strategy-full.md`.
