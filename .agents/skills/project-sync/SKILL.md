---
name: project-sync
description: |-
  Lite3 项目状态同步 SOP。触发：Dr Sun 说“同步状态/刷新热区/sync/文档没更新/补台账”。
  承接 .claude/commands/sync.md 到 Codex skills。
argument-hint: "[可选：需要同步的遗漏进展]"
user-invocable: true
context: inline
---

# Lite3 状态同步

读取以下状态源：

```
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
bigmemory/热区/近期改动.md
.pipeline/literature/index.md
.pipeline/experiments/
.pipeline/survey/
.pipeline/terminology/terminology.md
3_paper/main.tex
2_experiment/
```

同步内容：

1. 刷新热区三个文件，保持容量预算。
2. 检查新实验是否有 `.pipeline/experiments/` 台账。
3. 检查新文献是否已进入 `.pipeline/literature/index.md`。
4. 检查新术语是否进入 `.pipeline/terminology/terminology.md`。
5. AI 编辑 reviewed:true 文档时重置为 reviewed:false。

同步后运行 `bash .claude/scripts/sync-harness.sh --check`。
