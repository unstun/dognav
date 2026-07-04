---
name: literature-survey
description: |-
  Lite3 机器狗导航 DRL 文献调研 SOP。触发：Dr Sun 说“调研/搜论文/survey/找相关工作/补文献”。
  承接 .claude/commands/survey.md 到 Codex skills。
argument-hint: "[调研方向、关键词、时间窗或输出要求]"
user-invocable: true
context: inline
---

# Lite3 文献调研

先读取 `bigmemory/热区/状态简报.md`、`.pipeline/literature/index.md`、`.pipeline/terminology/terminology.md`。

执行前先给出搜索范围、关键词、目标数量和保存位置。需要确认时，Claude Code 使用 AskUserQuestion；Cursor 使用 AskQuestion；Codex Default mode 用简短中文问题。

执行原则：

1. 使用 `web-search` / `academic-researcher` / `paper-finder` / `biorxiv-database` 等合适 skill。
2. PDF 保存到 `1_survey/papers/<CitationKey>.pdf`。
3. 文献索引追加到 `.pipeline/literature/index.md`。
4. 综述输出写到 `.pipeline/survey/<topic>.md`，必须带 `origin` 和 `reviewed` frontmatter。
5. 付费墙或工具无法访问时列出检索项，不编造 DOI、URL 或结果。
