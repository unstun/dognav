---
name: "source-command-experiment-archive"
description: "实验归档：把训练、推理、评估结果记录成可复查但不死板的实验 capsule"
---

# source-command-experiment-archive

Use this skill when the user asks to run the migrated source command `experiment-archive`.

## Command Template

> **必须使用 AskUserQuestion 工具确认缺失的关键事实，不得用纯文字替代。**

你是 Lite3 机器狗导航 DRL Experiment Archivist。用户调用此命令时，目标不是继续训练，而是把一个已经发生的训练、推理或评估 run 归档清楚。

## 第一步：加载规范源

先读取：

```text
.agents/skills/experiment-archive/SKILL.md
.agents/skills/experiment-archive/templates/experiment_record.md
```

不要维护第二套归档规则；`.agents/skills/experiment-archive/` 是唯一规范源。

## 第二步：确认最小事实

如果对话里没有给全，用 `AskUserQuestion` 向 Dr Sun 补齐这些事实：

- 这是什么实验，不要只写代号。
- 从哪里来：parent checkpoint / source snapshot / contract。
- 跑了什么：task ID、训练或推理命令、conda env。
- 产物在哪：主 checkpoint、日志、TensorBoard、视频或关键图。
- 结果怎么看：推荐用哪个，哪个不推荐，为什么。
- 边界是什么：能 claim 什么，不能 claim 什么。

## 第三步：写归档

默认写到：

```text
.pipeline/experiments/YYYY-MM-DD/<experiment_id>.md
artifacts/<experiment_id>/
```

模板可以自由删改。不要为了填表凑空话；重要缺失项写“缺失 + 原因”。

`status: archived` 不是只写台账。必须确认 `artifacts/<experiment_id>/` 里有真实结果文件，并且关键 checkpoint、日志、TensorBoard、manifest 或视频/图表已被 git 跟踪。缺这些就写 `status: incomplete`。

## 第四步：校验

运行：

```bash
python .agents/skills/experiment-archive/scripts/validate_experiment_archive.py .pipeline/experiments/YYYY-MM-DD/<experiment_id>.md
```

严格审计才加 `--strict`。

## 第五步：结束汇报

最后只告诉 Dr Sun：

- 归档文件路径
- 主 checkpoint 与不推荐 checkpoint
- 一句话 claim 边界
