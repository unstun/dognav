#!/usr/bin/env bash
# ============================================================
# PreToolUse hook  --  搜索工具调用前注入策略提醒
# ------------------------------------------------------------
# 匹配     : WebSearch | WebFetch | mcp__grok-search__.*
# 目的     : AI 调搜索工具前提醒硬规则 #12 / gotchas 关键点,
#            防止(a) WebFetch/WebSearch 同批并行 403 级联
#                (b) 忘了用 Search Agent 隔离深度调研
#                (c) PDF 链接直抓导致解析失败
# 对照     : 原方案是 search-strategy.md 常驻加载,context 污染
# ============================================================
set -euo pipefail

# ------------------------------------------------------------
# 极简提醒 (≤150 字)
#   完整策略见 .claude/rules/search-strategy.md (常驻精简版)
#   或 .claude/rules/search-strategy-full.md (按需加载全文)
# ------------------------------------------------------------
cat <<'EOF'
=== 搜索策略提醒 (auto on search-tool) ===
- 深度/多源调研 → spawn web-search agent (sonnet),隔离 context,主会话只收 ≤800 字摘要
- 快速 1-2 条验证 → 直连 grok web_search
- WebFetch ≠ WebSearch 同批并行 (403 级联),各自独立批次
- PDF 链接大概率失败 → 换 HTML (arxiv.org/html/ 或 ar5iv)
- 付费墙 → 列检索项给 Dr Sun (Super Grok 网页处理)
- 详细决策流 → .claude/rules/search-strategy.md
EOF

exit 0
