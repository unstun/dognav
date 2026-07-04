---
description: 同行评审：审查 3_paper/main.tex，逐条讨论修改方案
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Lite3 机器狗导航 DRL Reviewer。论文审查结果需要和用户一起分析。

## 第一步：确认审查范围

```
3_paper/main.tex                         # 论文正文
3_paper/references.bib                   # 参考文献
.pipeline/experiments/                   # 实验台账（核对数据一致性）
.pipeline/terminology/terminology.md     # 术语规范
bigmemory/热区/状态简报.md               # 项目背景和声明的贡献点
```

用 `AskUserQuestion` 展示：

> **准备对以下内容进行同行评审**：
> - `3_paper/main.tex`（单文件论文）
>
> **审查维度**：技术贡献 / 实验充分性 / 写作质量 / 引用准确性 / 数据一致性 / 术语一致性
>
> 参照 `.claude/agents/reviewer.md` 中的评审标准。

选项：
- `开始审查`
- `增加特别关注的方面`
- `取消`

如果用户有额外关注点，记录后纳入审查。

## 第二步：执行审查

使用 `inno-paper-reviewer` skill，按 `.claude/agents/reviewer.md` 定义的 6 个维度逐一审查。

核对要点：
- `\cite{}` 引用是否存在于 `references.bib`
- 论文中的实验数据是否与 `.pipeline/experiments/` 台账一致
- 术语是否遵守 `.pipeline/terminology/terminology.md`

## 第三步：逐条讨论审查结果

**不要直接给出结论**，逐项和用户讨论：

> **审查结果（技术贡献：X/5）**
>
> 必须修改：
> 1. [问题 A]——你怎么看？

用 `AskUserQuestion`：
- `同意，修改`
- `我有不同看法`
- `这个问题不重要，跳过`

每个 major 问题都经过用户确认后，再批量修改。

## 第四步：决定最终结论

所有问题讨论完后，询问：

> **你的判断是**：

选项：
- `可以了，论文基本定稿`
- `还需要修改，我来描述改哪里`
- `需要大幅修改，重回 /write`
