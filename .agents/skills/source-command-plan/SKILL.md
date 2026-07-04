---
name: "source-command-plan"
description: "审视全局进展，以问答形式确认下一步方向"
---

# source-command-plan

Use this skill when the user asks to run the migrated source command `plan`.

## Command Template

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Lite3 机器狗导航 DRL Conductor。先全面读取项目状态，再和用户一起决定接下来做什么。

## 第一步：读取完整状态

```
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
bigmemory/热区/近期改动.md
.pipeline/literature/index.md
.pipeline/experiments/              # 扫描所有台账
.pipeline/terminology/terminology.md
```

## 第二步：生成状态摘要，和用户对话

用 `AskUserQuestion` 展示项目当前状态：

> **Lite3 机器狗导航 · 当前状态：[从状态简报提取]**
>
> **最近进展**：[1-2句话]
>
> **待解决**：[未关闭决策中的阻塞项，如有]
>
> **建议下一步**：[你认为最合适的下一步]

选项（根据实际情况动态生成）：
- `按建议继续：[具体下一步]`
- `我有其他想法`
- `先看看详细的实验/文献状态`

## 第三步：根据用户选择行动

- 选择继续：建议使用对应的命令（`/survey`、`/experiment`、`/write`、`/review`）
- 选择调整：`AskUserQuestion` 进一步了解想法
- 选择查看详情：列出 `.pipeline/experiments/` 和 `.pipeline/literature/index.md` 的内容摘要

## 最后：更新热区

如果对话中产生了新的方向决策或任务调整，更新 `bigmemory/热区/状态简报.md`。
