# ============================================================
# 联网检索策略（常驻摘要）
# 完整规范见 .claude/rules/search-strategy-full.md
# ============================================================

硬规则 #12 执行路径（优先级从高到低）：

1. **项目内**：Auggie MCP 语义检索 → 报错回退 Grep + Glob
2. **快速验证**（1-2 条事实）：Grok Search MCP 直连，`enable_planning=false`
3. **复杂问题**：Grok Search MCP，`enable_planning=true`
4. **深度调研**（多步/文献/技术选型）：spawn Search Agent（`model: sonnet`），返回 ≤800 字摘要 + 源 URL，主 context 只收摘要
5. **付费墙/403**：列清单交 Dr Sun 用 Super Grok 处理
6. **框架/库文档**：context7 MCP
7. **JS 渲染页面**：Playwright（最后手段）

隔离原则：深度调研必须走 sub-agent，禁止在主 session 中执行高噪声检索。

详见 `.claude/rules/search-strategy-full.md`
