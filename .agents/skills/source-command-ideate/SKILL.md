---
name: "source-command-ideate"
description: "生成并评估创新点，每步展示中间结果等用户参与决策"
---

# source-command-ideate

Use this skill when the user asks to run the migrated source command `ideate`.

## Command Template

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Lite3 机器狗导航 DRL Conductor。创新点的生成和最终选择都需要用户参与。

## 第一步：确认前置条件

```
bigmemory/热区/状态简报.md
.pipeline/literature/index.md           # 已有文献
.pipeline/survey/                       # 已有调研结论
.pipeline/terminology/terminology.md
```

用 `AskUserQuestion` 展示当前文献基础：

> 已有 X 篇文献，调研结论覆盖以下主题：
> [列出 .pipeline/survey/ 下的文件]
>
> 准备基于文献和调研结论生成创新方向。

选项：
- `确认，开始生成`
- `先看看现有调研结论再决定`
- `指定一个方向重点发展`

## 第二步：生成创新点

调用 `inno-idea-generation` skill，基于 `.pipeline/literature/index.md` 和 `.pipeline/survey/` 中的调研结论，生成 5 个候选创新方向。

## 第三步：展示 5 个 idea，等用户筛选

用 `AskUserQuestion` 展示：

> 生成了以下 5 个创新方向：
> 1. [Idea A]：...
> 2. [Idea B]：...
> ...
>
> 接下来对这些方向做新颖性和可行性评估。

选项：
- `全部评估`
- `只评估我感兴趣的（告诉我哪几个）`
- `这些方向不对，重新生成`

## 第四步：评估打分

调用 `inno-idea-eval` skill，对选定的 idea 打分（novelty / feasibility / impact 各 1-5 分）。

## 第五步：最终决策

展示评分结果，用 `AskUserQuestion` 询问：

> 评估结果：
> - [Idea A]：新颖 4 / 可行 3 / 影响 5
> - [Idea B]：新颖 5 / 可行 2 / 影响 4
> - ...
>
> 你倾向于选哪个方向？

选项列出各 idea 名称，加一个「我来描述自己的想法」。

用户选定后，更新 `bigmemory/热区/状态简报.md` 和 `bigmemory/热区/未关闭决策.md`，记录选择和被否决的方向。

## 提醒

- **多模型发散**：条件允许时，考虑用 Gemini（大 context）和 Codex（独立知识）各自生成 idea，再由 Codex 汇总去重——不同模型的知识盲区不同，ensemble 能提点。
- **对抗审查上限**：idea 评审建议不超过 3 轮，之后交 Dr Sun 拍板。避免无终局条件的互审循环（见 `.Codex/rules/gotchas.md`）。
- **先有 context 再发散**：idea 质量取决于 `.pipeline/survey/` 的调研深度。调研不够就 ideate 效果有限。
