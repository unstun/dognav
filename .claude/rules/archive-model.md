---
paths: ["bigmemory/**", ".claude/skills/archive/**"]
---
# 归档 agent 模型约束

`/archive` 的所有 agent 调用必须显式指定廉价模型：
- Claude Code 环境：`model: "sonnet"`
- Droid 环境：`gpt-5.4-mini`
禁止偷用 opus。Why: 归档是机械写入（读模板→按模板写→查重），无需强推理；5 worker 并行用 opus 成本高但质量零提升。
