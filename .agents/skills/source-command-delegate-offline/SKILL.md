---
name: "source-command-delegate-offline"
description: "为 Codex 独立终端生成 prompt，Dr Sun 复制到新终端跑 codex CLI（A 模式）"
---

# source-command-delegate-offline

Use this skill when the user asks to run the migrated source command `delegate-offline`.

## Command Template

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Lite3 机器狗导航 DRL Conductor。此命令用于**生成 Codex prompt 供 Dr Sun 在独立终端里执行**（A 模式）。适用于：

- 需要实时观察 Codex 输出（调试 / 交互式工作）
- 长时间运行，不希望占用主 Codex session
- 任务完全不需要回流到主 context

## 第一步：读取上下文

```
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
.pipeline/experiments/
.pipeline/terminology/terminology.md
```

## 第二步：展示计划，等待确认

用 `AskUserQuestion` 展示：

- **任务内容**：1-2 句话
- **上下文注入**：AGENTS.md 由 Codex CLI 自动加载；prompt 中额外附带的信息
- **输出位置**：Codex 产出写入哪里

选项：
- `确认，生成 prompt`
- `我来调整任务描述`
- `取消`

## 第三步：生成 Codex prompt（仅在确认后）

用代码块展示完整命令：

```
在新终端里 cd 到项目根目录（/Users/sun/tongbu/study/phdproject/machine-dog-nav），然后运行：

codex "[完整 prompt]"
```

> 需要后台运行时 Dr Sun 可自行 `nohup codex "..." &` 或在独立 tmux/terminal 中保留窗口——本地 `codex` CLI 无 `--background` 参数。Cursor 下 Codex 默认只走本命令/本模式, 不调用 `codex-rescue` 插件。

完整 prompt 格式：

```
[项目背景]
研究主题：Lite3 机器狗导航 DRL（从状态简报提取）
实验代码：按 nav baseline 子项目声明 Python module；默认目录 `2_experiment/nav_baselines/<topic>/`。
walking base policy 若被复用，必须声明来源 repo、commit、checkpoint 和冻结/微调边界。
实验目录：2_experiment/

[已有实验记录 - 避免重复]
（.pipeline/experiments/ 下最近 3 个台账的标题和结论）

[你的任务]
（确认后的任务描述）

[输出要求]
- 代码改动写入对应 nav 子项目目录。
- 实验结束后在 .pipeline/experiments/ 新建台账 YYYYMMDD_<topic>.md
- 遵守 .pipeline/terminology/terminology.md 中的术语规范
```

## 第四步：等待 Dr Sun 确认已跑起来

用 `AskUserQuestion` 询问：
- `我已经在新终端里跑起来了`
- `取消`

## 第五步：等待完成，读取结果

Dr Sun 确认完成后，检查产出：

```bash
ls .pipeline/experiments/ | tail -5
git log --oneline -5
```

向 Dr Sun 简要说明产出。

用 `AskUserQuestion` 询问：
- `接受结果`
- `需要修改某处`
- `这个结果有问题，放弃`

## 何时改用 /delegate

仅在 Codex / Droid 中, 若任务不需要 Dr Sun 实时观察（纯执行 + 结果摘要），可改用 `/delegate`——它 spawn `codex:codex-rescue` 子 agent 后台执行。**Cursor 不改用 `/delegate`**：默认仍由本命令生成 prompt, Dr Sun 手动输入 Codex。
