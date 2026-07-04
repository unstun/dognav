---
description: Conductor 规划任务，spawn codex:codex-rescue 子 agent 后台执行（B 模式）
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**
> **Cursor 禁用本命令作为 Codex 默认路径**：Cursor 下使用 `/delegate-offline` 风格, 只生成 prompt 供 Dr Sun 手动输入 Codex。

你是 Lite3 机器狗导航 DRL Conductor。此命令用于**将代码 / 实验任务委派给 Codex 执行**——主 Claude 只做规划和结果综合，节约 Opus token（B 模式）。

## 第一步：读取上下文

```
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
.pipeline/experiments/
.pipeline/terminology/terminology.md
```

## 第二步：展示计划，等待确认

用 `AskUserQuestion` 向 Dr Sun 展示将要委派的任务摘要：

- **任务内容**：1-2 句话描述将交给 Codex 做什么
- **上下文注入**：AGENTS.md 通道自动提供硬规则与术语；prompt 中额外附带的信息
- **输出位置**：Codex 产出写入哪里

选项：
- `确认，spawn 子 agent 执行`
- `我来调整任务描述`
- `取消`

## 第三步：spawn codex:codex-rescue 子 agent（仅在确认后）

调用 Agent 工具，参数如下：

- `subagent_type`: `codex:codex-rescue`
- `description`: ≤6 字任务概括
- `prompt`: 完整任务描述，需包含
  - 项目背景（从状态简报提取）
  - 实验代码按 nav baseline 子项目声明 Python module；默认目录 `2_experiment/nav_baselines/<topic>/`
  - walking base policy 若被复用，必须声明来源 repo、commit、checkpoint 和冻结/微调边界
  - 实验目录 `2_experiment/`
  - `.pipeline/experiments/` 最近 3 个台账的标题和结论（避免重复）
  - 任务描述
  - 输出要求：代码改动写入对应 nav 子项目目录；实验台账 `.pipeline/experiments/YYYYMMDD_<topic>.md`；遵守 `.pipeline/terminology/terminology.md`
- `run_in_background`: `true`（后台执行，主 session 可继续做别的；完成后系统自动通知）

## 第四步：等待完成，读取结果

子 agent 返回后，读取其摘要，并检查落盘产出：

```bash
ls .pipeline/experiments/ | tail -5
git log --oneline -5
```

向 Dr Sun 简要说明：做了什么、产出了哪些文件、有没有问题。

用 `AskUserQuestion` 询问：
- `接受结果，继续下一步`
- `需要修改某处`
- `这个结果有问题，放弃`

## 何时改用 /delegate-offline

若任务需要 Dr Sun 在独立终端里全程观察 Codex 输出（调试 / 交互 / 长时间训练），或当前 CLI 是 Cursor，改用 `/delegate-offline`——它只生成 prompt，由 Dr Sun 在独立终端跑 `codex` CLI。
