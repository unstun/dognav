---
paths: [".pipeline/survey/**", ".pipeline/literature/**", "1_survey/**", "**/*literature*", "**/*survey*"]
---
# ============================================================
# 联网检索策略（完整版）
# 硬规则 #12 详细决策框架
# ============================================================

核心原则：**默认联网，信息质量优先**。用 agent 隔离控制 context 膨胀，而非限制联网次数。

## 决策流

```
查询进来
  │
  ├─ 项目内已有信息？ ──→ Auggie MCP 语义检索
  │     └─ Auggie MCP 报错 → Grep + Glob 回退
  │
  ├─ 快速验证（1-2 条事实、概念确认）
  │     └→ Grok Search MCP 直连（结果轻量，直接进 Opus context）
  │         ├─ 精确问题：enable_planning=false
  │         └─ 复杂问题：enable_planning=true
  │
  ├─ 深度调研（多步/多源/技术选型/文献搜索）
  │     └→ spawn Search Agent (model=sonnet)
  │         → 多轮 WebSearch + WebFetch + Grok Search
  │         → 返回 ≤800 字摘要 + 源 URL
  │         → Opus context 只接收摘要，不膨胀
  │
  ├─ 付费墙 / 工具受限页面（WebFetch 403、需登录等）
  │     └→ 列检索项清单交 Dr Sun 用 Super Grok 网页端处理
  │         → Dr Sun 返回结果后 AI 继续处理
  │         → Why: Super Grok 已订阅，零 token 开销，质量更高
  │
  ├─ 框架/库文档查询 ──→ context7 MCP（比通用搜索更精确）
  │
  └─ 必须 JS 渲染的页面 ──→ Playwright MCP（最后手段）
```

## 可用工具清单

| 工具 | 类型 | 适用场景 | Context 影响 |
|------|------|----------|-------------|
| Auggie MCP (`mcp__auggie.codebase_retrieval`) | MCP | 项目内语义搜索；Codex 当前 server 为 `auggie`，实际 transport 以 `codex mcp get auggie` 为准；`codebase-retrieval` 仅作能力名或旧写法 | 依赖 Auggie 索引 |
| Grok Search (`web_search`) | MCP | 快速验证 + 综合答案 | 轻量（直连） |
| Grok Search (`get_sources`) | MCP | 验证源 URL 质量 | 极轻 |
| WebSearch | 内置 | 广泛搜索获取链接列表 | 中等 |
| WebFetch | 内置 | 读具体 URL 精提取 | 受 prompt 精确度控制 |
| context7 (`resolve-library-id` / `query-docs`) | MCP | 框架/库官方文档 | 轻量 |
| Playwright | MCP | JS 渲染页面 | 极重，最后手段 |

## Grok Search MCP 使用规范

- 精确问题：`enable_planning=false`，快速返回
- 复杂/多面问题：`enable_planning=true`，自动 6 阶段规划
- `platform` 参数限定搜索容易超时，非必要不用
- 搜索后如需验证源质量，调 `get_sources` 拿 URL 列表

## Search Agent 规范

**所有联网搜索 Agent 一律 `model: "sonnet"`**，禁用 opus。
Why: 搜索是 IO 密集型任务（等网络、解析页面），不需要 opus 级推理；sonnet 足够且成本低，隔离 context 后主会话不受影响。

深度调研时 spawn Sonnet subagent（skill: `web-search`），规范：

- Agent 自主选择 WebSearch / WebFetch / Grok Search 最佳组合
- 输出 ≤800 字摘要 + 源 URL 列表
- 引号/数据必须来自 WebFetch 原文或 Grok 返回内容，禁 LLM 编造
- Agent 内部 WebFetch ≤5 次（控制 subagent 自身 context）
- 搞不定的问题列清单上报，由 Dr Sun 或主 AI 决定下一步

## 防膨胀机制

- **快查路径**：Grok 直连结果轻量，可接受进 Opus context
- **深度路径**：Search Agent 隔离，主 context 只接收精简摘要
- **WebFetch prompt 必须精确**：模糊 prompt 导致全文灌入，精确 prompt 是手动版 dynamic filtering
- **禁混 WebFetch/WebSearch 同批并行**：WebFetch 403 会级联拖垮同批调用

## 禁止项

- 禁凭 AI 训练记忆回答专业问题（硬规则 #8）
- 禁为付费墙文献使用 Playwright（token 成本过高）
- PDF 链接大概率解析失败，优先 HTML 版本（如 `arxiv.org/html/`）
