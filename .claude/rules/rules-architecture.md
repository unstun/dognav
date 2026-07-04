---
paths:
  - ".claude/rules/**"
  - "CLAUDE.md"
  - "AGENTS.md"
---
# CLAUDE.md 维护规范

## 注入机制

- CLAUDE.md 以 user message 注入(非 system prompt),Claude 逐条判断相关性。
- `.claude/rules/*.md` 无 `paths` 则每次会话全量加载;有 `paths` 则仅在读取匹配文件时注入。
- 指令预算约 150-200 条,根文件目标 ≤100 行。

## 写作原则

- **正面框架优于负面**:MUST 优于 NEVER。NEVER 占比应 <10%。
- **附加理由(Why)**:帮助 AI 判断边界情况。
- **IMPORTANT/YOU MUST 有效但滥用稀释效果**:仅用于真正关键的规则。
- **首尾偏差(U-shaped)**:最重要的规则放首尾。

## 内容取舍

**有效内容**(应保留):
- 非显而易见的工具决策
- 非常规配置和项目特有约束
- AI 反复犯错的规则

**无效内容**(应删除或外置):
- 目录结构/架构概述(agent 善于自发现)
- 叙事性背景段落
- 过时的结构描述
- linter 可执行的代码风格规则

## Advisory vs Deterministic

- CLAUDE.md 是 advisory,hooks 是 deterministic。
- 必须零例外执行的机械性规则应 hook 化。
