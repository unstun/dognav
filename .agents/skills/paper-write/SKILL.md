---
name: paper-write
description: |-
  Lite3 机器狗导航 DRL 论文写作 SOP——按需推进 3_paper/main.tex, 每步确认后再继续。
  触发: Dr Sun 说 "写论文/写一下 method/写 results/补 abstract/写引言/写 related work",
  或 AI 进入"论文写作"阶段需要按节推进。
  区别于 `inno-paper-writing` / `ml-paper-writing` skill (那是通用 ML 论文写作), 本 skill 专注 Lite3 项目论文 + 主 session 协调 + 大段外派 CLI。
argument-hint: "[可选: 想写的章节, 如 'method' / 'experiments']"
user-invocable: true
context: inline
---

# Lite3 论文写作 · 按节推进

> 镜像自 `.claude/commands/write.md`，让 Cursor / Codex / 其他 CLI 也能加载本 SOP。
> 受众: 本项目主 session 调本 skill 启动一次"论文写作对话"。

> Claude Code 使用 AskUserQuestion；Cursor 使用 AskQuestion；Codex Default mode 没有问答工具时，用简短中文问题确认必要信息。

你是 Lite3 机器狗导航 DRL Paper Writer 协调器。写作按需推进, 每步完成后确认再继续。**Cursor 主 session 不直接生成正文 (token 极贵), 大段写作外派 gemini-do**。

## 第一步: 定向检索 + 读取写作上下文

> **AGENTS.md 硬规则 #5**: 本 skill 命中"准备写论文"白名单, **必须先调 `memory-retrieval` skill 做定向检索**, 禁止直读 `bigmemory/热区/*` 与 `.pipeline/*` 绕过。

工作流:

1. **先 invoke `memory-retrieval` skill**, 传入查询意图:
   ```
   memory-retrieval args: "Lite3 论文 <章节> / 当前贡献 claim / 未关闭决策 / 关联实验台账 / Contract 状态"
   ```
2. **再按 memory-retrieval 返回的精选清单 Read 具体文件 + 直读论文资源**:
   ```
   # memory-retrieval 提供精选 (bigmemory + .pipeline)
   bigmemory/热区/状态简报.md (subagent 已核对冷区)
   .pipeline/literature/index.md            # 参考文献索引
   .pipeline/experiments/                   # subagent 标出关联台账
   .pipeline/contracts/                     # subagent 标出 claim 对应 Contract
   .pipeline/terminology/terminology.md     # 术语规范

   # 论文本体直读 (memory-retrieval 不管 3_paper/)
   3_paper/main.tex                         # 论文主文件 (单文件结构, 不是 sections/*.tex)
   3_paper/writing_rules.md                 # 写作硬约束 (强制遵守)
   3_paper/references.bib                   # BibTeX 引用库
   ```

## 第二步: 确认写作范围

用问答工具展示:

> **论文当前状态**: [从 main.tex 提取各节完成度]
>
> 你想写/修改哪个部分?

选项:
- `Abstract + Introduction`
- `Related Work`
- `Methodology`
- `Experiments & Results`
- `Conclusion`
- `我来指定具体修改内容`

## 第三步: 按 paper-writer agent 分诊路由

按 `.claude/agents/paper-writer.md` "## 接到任务时的自助分诊" 节, 根据本节预估字数路由:

| 任务规模 | 路由 |
|---|---|
| ≤500 字单段编辑 / 术语替换 / cite 插入 | 主 session 自己改 + humanizer skill 过 |
| >500 字正文生成 / 段落重写 / 单节起草 / 整章重写 / 写引言摘要 | **强制外派 `gemini-do` skill** (Gemini 长上下文) |
| 写代码片段 / 复杂公式 / 大表格 | **Cursor 下生成 Codex 手动任务包**（不调用 codex-rescue / Task） |

**阈值**: 与 `cli-cursor.md` ">500 字正文外派" 边界一致, 不再分 500-2000 / >2000 两档——避免本地起草然后被 codex review 标"违反 >500 外派"。

每节开始前告知用户依赖的数据来源:

> 现在写 **[节名]** (路由: <自己 / gemini-do / Codex 手动任务包>), 基于:
> - 数据: [.pipeline/experiments/ 哪个台账]
> - Contract: [.pipeline/contracts/ 哪个对应 claim]
> - 引用: [.bib 关键 cite key]

写作规范:
- 使用 `inno-paper-writing` 和 `scientific-writing` skills 提供学术语气模板
- **强制遵守** `3_paper/writing_rules.md` 和 `.pipeline/terminology/terminology.md`
- 引用格式: `\cite{AuthorYear}` 对应 `3_paper/references.bib` 中的 key
- 实验数据**必须**来自 `.pipeline/experiments/` 台账, 严禁捏造
- 实验 claim **必须**有 `.pipeline/contracts/<topic>.md` 中 success/failure signal 支撑

每节完成后, 用问答工具询问:

> **[节名] 已完成** (路由: <写作路径>, 字数: <数字>, AI 腔检查: <已跑/未跑>)。你想:

选项:
- `继续写下一节`
- `先看看这节写得怎么样`
- `这节有问题, 需要修改`
- `暂停, 稍后继续`

## 第四步: 图表和引用

写作完成后, 询问:

> 正文已完成。接下来:

选项:
- `生成图表到 3_paper/figures/` (调 inno-figure-gen skill)
- `做引用审查 (调 inno-reference-audit skill)`
- `两个都做`
- `进入 paper-review skill 做同行评审`

## 关键约束 (规则 #20 / #22)

- **每段论文 Dr Sun 必须过目** (规则 #22 human-in-the-loop)——外派 CLI 写完不能直接 commit
- **实验 claim 必须有 Contract 支撑** (规则 #20)——CLI 写正文时必须显式喂入 Contract 内容让它对照
- **AI 腔检查**: 大段写作 (>500 字) 完成后必须跑 `humanizer` skill

## CLI 适配

| CLI | 调用方式 |
|---|---|
| Codex | `/write` slash command 或 invoke 本 skill |
| Cursor | invoke 本 skill, 主 session 协调；Codex 相关任务只生成供 paste 到 Codex App 的任务包 |
| Codex App | paste 任务包（paper-write 语境） |

**为什么必须主 session 协调**: Contract 对照 + Dr Sun review 必须主 session 跑——只有主 session 拿全 .pipeline/contracts/ 的上下文。具体的"写"动作 (token 重活) 才外派 CLI。
