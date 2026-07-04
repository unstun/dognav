---
name: paper-review
description: |-
  Lite3 机器狗导航 DRL 论文同行评审 SOP——对 3_paper/main.tex 做 6 维度审查并和 Dr Sun 逐条讨论。
  触发: Dr Sun 说 "审一下论文/做评审/review 论文/检查论文/查 cite 完整性/查实验数据一致性",
  或 AI 进入"论文定稿前评审"阶段需要全方位检查。
  区别于 `dual-review` skill (那是审 git diff 用的), 本 skill 专注 Lite3 论文同行评审 + Dr Sun 逐条决策流。
argument-hint: "[可选: 你想优先关注的方面，如 'related work 部分' / '只查引用']"
user-invocable: true
context: inline
---

# Lite3 论文同行评审 · 逐条讨论

> 镜像自 `.claude/commands/review.md`，让 Cursor / Codex / 其他 CLI 也能加载本 SOP。
> 受众: 本项目主 session 调本 skill 启动一次"论文评审对话"。

> Claude Code 使用 AskUserQuestion；Cursor 使用 AskQuestion；Codex Default mode 没有问答工具时，用简短中文问题确认必要信息。

你是 Lite3 机器狗导航 DRL Reviewer。论文审查结果需要和 Dr Sun 一起分析。

## 第一步: 定向检索 + 确认审查范围

> **AGENTS.md 硬规则 #5**: 本 skill 命中"做评审 / 检查论文"白名单, **必须先调 `memory-retrieval` skill 做定向检索**, 禁止直读 `bigmemory/热区/*` 与 `.pipeline/*` 绕过。

工作流:

1. **先 invoke `memory-retrieval` skill**, 传入查询意图:
   ```
   memory-retrieval args: "Lite3 论文声明的 contribution / 关联实验台账数字 / Contract status / 术语规范现况"
   ```
2. **再按 memory-retrieval 返回的精选清单 Read 具体文件 + 直读论文资源**:
   ```
   # memory-retrieval 提供精选 (bigmemory + .pipeline)
   bigmemory/热区/状态简报.md (subagent 已核对冷区)
   .pipeline/experiments/                   # subagent 标出引用过的台账
   .pipeline/contracts/                     # subagent 标出 claim 对应 Contract
   .pipeline/terminology/terminology.md

   # 论文本体直读
   3_paper/main.tex                         # 论文正文
   3_paper/references.bib                   # 参考文献
   ```

用问答工具展示:

> **准备对以下内容进行同行评审**:
> - `3_paper/main.tex` (单文件论文)
>
> **审查维度**: 技术贡献 / 实验充分性 / 写作质量 / 引用准确性 / 数据一致性 / 术语一致性
>
> 参照 `.codex/agents/reviewer.toml` 与 `.claude/agents/reviewer.md` 中的评审标准。

选项:
- `开始审查`
- `增加特别关注的方面`
- `取消`

如果用户有额外关注点, 记录后纳入审查。

## 第二步: 执行审查 (按 reviewer agent 分诊)

按 `.claude/agents/reviewer.md` "## 接到任务时的自助分诊" 节执行:

| 维度 | 路径 |
|---|---|
| 引用准确性 (\cite{} ↔ .bib) | 自己 Grep + 比对 |
| 数据一致性 (论文数字 ↔ 台账) | 自己 Read 台账 + diff |
| 术语一致性 | 自己 Grep terminology.md |
| 技术贡献 / 实验充分性 / 写作质量 | **主 session 生成 Codex + Gemini 双审任务包**；Dr Sun 手动跑 CLI 后回贴 (跨族交叉, 见下方说明) |

严禁: 主 session / sonnet 自己跑技术贡献 / 实验充分性 / 写作质量这三维度详评 (同族盲区, 失去 ensemble 意义)。Cursor 下也严禁主 session 调 `codex-rescue` 插件代跑。

### 论文审查为何不走 `dual-review` skill

`dual-review` skill 设计场景是**审 git diff** (Codex/Gemini 看本次改动正确性), 输入是 `git diff` 文本。但论文同行评审需要喂入**完整 `3_paper/main.tex` + 实验台账 + Contract**, 评审对象是论文质量, 不是 diff——直接复用 `dual-review` 会让两个模型只看到 diff, 评审走偏。

**正确做法 (本 skill v2)**: 主 session 直接并行 dispatch:

```
├─ Codex 手动任务包
│   - 主 session 生成 prompt: main.tex 全文 + 关键 .pipeline/contracts/<topic>.md + .pipeline/experiments/ 台账
│   - Dr Sun paste 到 Codex App
│   - 评审维度: 技术贡献 (Codex 偏代码细节 / 技术正确性)
│
└─ gemini-do skill (并行)
    - 喂入: 同上 (完全相同的 prompt + 资料, 保证公平交叉)
    - 评审维度: 实验充分性 / 写作质量 (Gemini 偏架构 / 长链路推理)

→ 主 session 拿到双模型输出后整合, 标出双方分歧 + 一致点 → 进入第三步逐条讨论
```

两个 CLI 拿到的 prompt 必须**逐字相同**, 仅模型族不同, 才能对比认知盲区。

## 第三步: 逐条讨论审查结果

**不要直接给出结论**, 逐项和 Dr Sun 讨论:

> **审查结果 (技术贡献: X/5)**
>
> 必须修改:
> 1. [问题 A]——你怎么看?

用 AskUserQuestion / AskQuestion 工具:
- `同意, 修改`
- `我有不同看法`
- `这个问题不重要, 跳过`

每个 major 问题都经过用户确认后, 再批量修改。

## 第四步: 决定最终结论

所有问题讨论完后, 询问:

> **你的判断是**:

选项:
- `可以了, 论文基本定稿`
- `还需要修改, 我来描述改哪里`
- `需要大幅修改, 重回 paper-write skill`

## CLI 适配

| CLI | 调用方式 |
|---|---|
| Codex | `/review` slash command 或 invoke 本 skill |
| Cursor | invoke 本 skill, 主 session 协调 + 生成 Codex/Gemini 手动审查任务包 (不走 codex-rescue 插件) |
| Codex App | paste 任务包（paper-review 语境；Codex 内也能跟着做） |

**为什么必须主 session**: 本 skill 是"逐条讨论"流程, 必须主 session 跑——只有主 session 能直接和 Dr Sun 对话。详细审查的 LLM 工作 (技术 / 实验 / 写作三维度) 由主 session 生成任务包并由 Dr Sun paste 到 Codex App 或手动运行 Gemini, 而不是间接走 `dual-review` skill (那个 skill 锁定输入是 git diff, 不适合审完整论文)。
