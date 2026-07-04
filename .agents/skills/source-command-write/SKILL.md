---
name: "source-command-write"
description: "论文写作：按需推进 3_paper/main.tex，每步确认后再继续"
---

# source-command-write

Use this skill when the user asks to run the migrated source command `write`.

## Command Template

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Lite3 机器狗导航 DRL Paper Writer。写作按需推进，每步完成后确认再继续。

## 第一步：读取写作上下文

```
bigmemory/热区/状态简报.md
3_paper/main.tex                         # 论文主文件（单文件结构）
3_paper/writing_rules.md                 # 写作硬约束（强制遵守）
.pipeline/literature/index.md            # 参考文献索引
.pipeline/experiments/                   # 实验台账（真实数据来源）
.pipeline/terminology/terminology.md     # 术语规范（强制遵守）
3_paper/references.bib                   # BibTeX 引用库
```

**注意**：论文是**单文件结构**（`3_paper/main.tex`），不是 `sections/*.tex` 分文件。

## 第二步：确认写作范围

用 `AskUserQuestion` 展示：

> **论文当前状态**：[从 main.tex 提取各节完成度]
>
> 你想写/修改哪个部分？

选项：
- `Abstract + Introduction`
- `Related Work`
- `Methodology`
- `Experiments & Results`
- `Conclusion`
- `我来指定具体修改内容`

## 第三步：按节逐步执行

每节开始前告知用户依赖的数据来源：

> 现在写 **[节名]**，基于：[数据来源文件]

写作规范：
- 使用 `inno-paper-writing` 和 `scientific-writing` skills
- **强制遵守** `3_paper/writing_rules.md` 和 `.pipeline/terminology/terminology.md`
- 引用格式：`\cite{AuthorYear}` 对应 `3_paper/references.bib` 中的 key
- 实验数据必须来自 `.pipeline/experiments/` 台账，严禁捏造

每节完成后，用 `AskUserQuestion` 询问：

> **[节名] 已完成**。你想：

选项：
- `继续写下一节`
- `先看看这节写得怎么样`
- `这节有问题，需要修改`
- `暂停，稍后继续`

## 第四步：图表和引用

写作完成后，询问：

> 正文已完成。接下来：

选项：
- `生成图表到 3_paper/figures/`
- `做引用审查（inno-reference-audit）`
- `两个都做`
- `进入 /review 做同行评审`
