---
name: idea-routing
description: |-
  Lite3 机器狗导航 DRL 创新方向生成与筛选 SOP。触发：Dr Sun 说“想 idea/创新点/选方向/ideate”。
  承接 .claude/commands/ideate.md 到 Codex skills。
argument-hint: "[可选：指定研究方向、约束或候选 idea]"
user-invocable: true
context: inline
---

# Lite3 创新方向筛选

先读取 `bigmemory/热区/状态简报.md`、`.pipeline/literature/index.md`、`.pipeline/survey/`、`.pipeline/terminology/terminology.md`。

流程：

1. 确认当前文献和调研基础。
2. 调用 `inno-idea-generation` 生成候选方向。
3. 调用 `inno-idea-eval` 做 novelty / feasibility / impact 评估。
4. 只记录 Dr Sun 已确认的方向；未确认方向作为候选保留。
5. 如形成新决策，更新 `bigmemory/热区/状态简报.md` 和 `bigmemory/热区/未关闭决策.md`。

需要确认时，Claude Code 使用 AskUserQuestion；Cursor 使用 AskQuestion；Codex Default mode 用简短中文问题。
