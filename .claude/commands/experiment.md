---
description: 实验循环：展示实验方案后确认，每轮结果回来后再决定继续/停止
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Lite3 机器狗导航 DRL Experiment Driver。实验不能盲目启动，每轮都需要确认。

## 第一步：读取当前状态

```
bigmemory/热区/状态简报.md
.pipeline/experiments/                  # 已有实验台账（避免重复失败配置）
.pipeline/terminology/terminology.md
```

用 `AskUserQuestion` 展示当前实验背景：

> **当前状态**：[从状态简报提取]
> **已有实验**：[.pipeline/experiments/ 台账数，或"尚无"]
>
> 准备进入实验循环。第一步是设计实验方案。

选项：
- `继续，先设计方案`
- `我先描述一下我想要的实验配置`
- `取消`

如果用户有自己的配置描述，先记录下来再进入设计。

## 第二步：设计实验方案

根据 `bigmemory/热区/状态简报.md` 和 `.pipeline/experiments/` 中的历史台账（避免重复失败配置），设计实验方案。

用 `AskUserQuestion` 展示方案摘要，等确认：

> **实验方案**：
> - 目标：[验证什么假设]
> - Config: use the baseline-specific config location recorded in that baseline's `CURRENT_CODE.yaml`.
> - 算法：PPO / SAC
> - 仿真环境：Isaac Lab / MuJoCo
> - 评估指标：...
>
> 确认后开始实现和运行。

选项：
- `方案可以，开始实现`
- `调整某个配置`
- `重新设计方案`

## 第三步：实现并运行

代码改动写入 `2_experiment/nav_baselines/<topic>/` 或 Contract 指定的 nav 子项目目录。若复用 walking base policy，必须在 Contract 和台账中记录来源 repo、commit、checkpoint、冻结/微调边界。通过 `/delegate` 或远程任务包执行。

远程执行参照 `.claude/rules/experiment.md` 中的常用命令模板。

## 第四步：记录实验台账

每轮实验结束后，在 `.pipeline/experiments/` 新建台账 `YYYYMMDD_<topic>.md`，格式参照 `.claude/agents/experiment-driver.md`。

用 `AskUserQuestion` 请 Dr Sun 补充人工观察：

> **实验 [主题] 已记录到 `.pipeline/experiments/YYYYMMDD_<topic>.md`**
>
> 请补充你的人工观察（训练曲线趋势、异常现象、直觉判断等）：

选项：
- `我来写注释`
- `暂时跳过，之后再补`

## 第五步：结果评估，决定下一步

用 `AskUserQuestion` 展示结果：

> **最新实验结果**：[关键指标]
> **状态**：达标 / 未达标

选项（未达标时）：
- `调整超参，再跑一轮`
- `修改实验设计，重新来`
- `结果够用了，进入写作`

选项（达标时）：
- `进入 /write 写论文`
- `还想多跑几组对比实验`

## 提醒

- **Baseline 先行**：新实验前建议先复现 baseline，建立可靠锚点。Baseline 复现与新实验开发尽量隔离。
- **数据版本锁定**：所有模型用完全相同的预处理数据，随机种子显式固定并记录。
- **误差线**：条件允许时多轮运行取均值±标准差，单次结果说服力有限。
- **Contract 检查**：实验前留意 `.pipeline/contracts/` 是否有对应 Research Contract（详见硬规则 #20 和 `.claude/rules/experiment.md`）。
