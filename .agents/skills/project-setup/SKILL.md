---
name: project-setup
description: |-
  初始化或修复 Lite3 academic harness 目录结构。触发：Dr Sun 说“初始化 harness/setup/缺目录/重建脚手架”。
  承接 .claude/commands/setup.md 到 Codex skills。
argument-hint: "[可选：需要检查或初始化的范围]"
user-invocable: true
context: inline
---

# Lite3 Harness 初始化

检查并补齐：

```
bigmemory/热区
bigmemory/冷区/{改动记录,踩坑记录,调研记录,心路历程,里程碑}
.pipeline/{terminology,literature,survey,experiments,contracts,codex_tasks}
.claude/{agents,commands,rules,scripts,skills}
.codex/{agents,hooks,rules}
.agents/skills
```

已有文件不得覆盖。缺失模板按 `AGENTS.md`、`bigmemory/格式规范.md`、`.pipeline/README.md` 的现有约定生成。

涉及 `.pipeline/` 结构增删时，需先取得 Conductor 授权。
