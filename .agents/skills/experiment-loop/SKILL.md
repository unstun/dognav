---
name: experiment-loop
description: |-
  Lite3 机器狗导航 DRL 实验循环 SOP——展示实验方案后确认, 每轮结果回来后再决定继续/停止。
  触发: Dr Sun 说 "跑实验/跑训练/做对比实验/换超参再跑/做 ablation",
  或 AI 进入"实验执行"阶段需要正式启动实验循环 (硬规则 #20: 实验前必须有 Contract approved)。
argument-hint: "[可选: 你想跑的实验描述, 如 'PPO baseline' / 'reward shaping ablation']"
user-invocable: true
context: inline
---

# Lite3 实验循环 · 逐轮确认

> 镜像自 `.claude/commands/experiment.md`，让 Cursor / Codex / 其他 CLI 也能加载本 SOP。
> 受众: 本项目主 session 调本 skill 启动一次"实验循环对话"。

> Claude Code 使用 AskUserQuestion；Cursor 使用 AskQuestion；Codex Default mode 没有问答工具时，用简短中文问题确认必要信息。

你是 Lite3 机器狗导航 DRL Experiment Driver。实验不能盲目启动, 每轮都需要确认。

## 前置检查 (硬规则 #20)

进入实验循环前, **必须**确认:

```
.pipeline/contracts/<topic>.md   # 必须有 Research Contract, status: approved 或 frozen
```

如果没有 Contract 或 status: draft, **拒绝**进入实验循环, 让 Dr Sun 先去 contracts/ 走 approved 流程。

## 第一步: 定向检索 + 读取当前状态

> **AGENTS.md 硬规则 #5**: 本 skill 命中"做实验决策 / 跑训练"白名单, **必须先调 `memory-retrieval` skill 做定向检索**, 禁止直读 `bigmemory/热区/*` 与 `.pipeline/*` 绕过。

工作流:

1. **先 invoke `memory-retrieval` skill**, 传入查询意图:
   ```
   memory-retrieval args: "Lite3 实验阶段进展 / 已有 baseline / 失败配置黑名单 / 当前 Contract status"
   ```
2. **再按 memory-retrieval 返回的精选清单 Read 具体文件**:
   ```
   bigmemory/热区/状态简报.md (subagent 已核对冷区)
   .pipeline/experiments/                  # subagent 标出关键台账, 避免重复失败配置
   .pipeline/contracts/                    # subagent 标出当前 active Contract
   .pipeline/terminology/terminology.md
   ```

用问答工具展示当前实验背景:

> **当前状态**: [从状态简报提取]
> **已有实验**: [.pipeline/experiments/ 台账数, 或"尚无"]
> **当前 Contract**: [.pipeline/contracts/<topic>.md 的 hypothesis 摘要]
>
> 准备进入实验循环。第一步是设计实验方案。

选项:
- `继续, 先设计方案`
- `我先描述一下我想要的实验配置`
- `取消`

如果用户有自己的配置描述, 先记录下来再进入设计。

## 第二步: 设计实验方案

根据 `bigmemory/热区/状态简报.md` 和 `.pipeline/experiments/` 中的历史台账 (避免重复失败配置), 设计实验方案。

用问答工具展示方案摘要, 等确认:

> **实验方案**:
> - 目标: [验证什么假设——必须对应 Contract 的某条 hypothesis]
> - Config: use the nav baseline config location recorded in the Contract.
> - 算法: PPO / SAC
> - 仿真环境: Isaac Lab / MuJoCo
> - 评估指标: ...
> - **success signal**: [Contract 锁定的成功条件]
> - **failure signal**: [Contract 锁定的失败条件——独立于 success]
>
> 确认后开始实现和运行。

选项:
- `方案可以, 开始实现`
- `调整某个配置`
- `重新设计方案`

## 第三步: 实现并运行

按 `.codex/agents/experiment-driver.toml` 与 `.claude/agents/experiment-driver.md` 的 CLI 适配节路由:

| 任务 | Cursor 推荐路径 |
|---|---|
| 写实验代码 / 改 PPO / SAC 实现 | 主 session 生成 **Codex 手动任务包**；Dr Sun paste 到 Codex App，回贴 diff/验证日志 |
| 跑长训练 (24h+ GPU) | 主 session 生成 `remote-ssh`/tmux/nohup 命令包；Dr Sun 本机终端执行 |
| 改少量超参 / config | 主 session 直接做 |

**不在主 session 跑长训练, 也不在 Cursor 主 session 调 Codex 插件代跑**——按硬规则 #21 与 Cursor token 纪律, 主 session 只给任务包 + 判据, 只审核回传结果。

## 第四步: 记录实验台账

每轮实验结束后, 在 `.pipeline/experiments/` 新建台账 `YYYYMMDD_<topic>.md`, 格式参照 `.claude/agents/experiment-driver.md`。台账必须包含:

- Contract 引用 (链接 .pipeline/contracts/)
- success / failure 判定 (按 Contract 锁定的 signal)
- 关键 metric + 训练曲线
- 异常 / 直觉判断

用问答工具请 Dr Sun 补充人工观察:

> **实验 [主题] 已记录到 `.pipeline/experiments/YYYYMMDD_<topic>.md`**
>
> 请补充你的人工观察 (训练曲线趋势 / 异常现象 / 直觉判断等):

选项:
- `我来写注释`
- `暂时跳过, 之后再补`

## 第五步: 结果评估, 决定下一步

按 Contract 锁定的 success / failure signal 严格判定:

> **最新实验结果**: [关键指标]
> **Contract 判定**: success / failure / 部分达标
> (failure 不是 success 的反面——必须独立判定)

选项 (failure 时):
- `调整超参, 再跑一轮`
- `修改实验设计 (注意: 可能需要更新 Contract → v2)`
- `Contract 判 failure, 进入写作 (failure 也是结果, 不可包装为 success)`

选项 (success 时):
- `进入 paper-write skill 写论文`
- `还想多跑几组对比实验`

## 关键提醒

- **Baseline 先行**: 新实验前先复现 baseline, 建立可靠锚点。Baseline 复现与新实验开发尽量隔离
- **数据版本锁定**: 所有模型用完全相同的预处理数据, 随机种子显式固定并记录
- **误差线**: 条件允许时多轮运行取均值±标准差, 单次结果说服力有限
- **Contract 不可改**: 实验中**禁止**修改 Contract success / failure signal——禁不住"AI 合理化"的试探 (AGENTS.md 注意事项 #5)
- **failure 不是 success 反面**: 必须独立定义 (AGENTS.md 硬规则 #20)

## CLI 适配

| CLI | 调用方式 |
|---|---|
| Codex | `/experiment` slash command 或 invoke 本 skill |
| Cursor | invoke 本 skill, 协调器主 session 跑, 代码/远端执行只生成 paste 到 Codex App 的任务包 / 终端任务包 |
| Codex App | paste 任务包（experiment-loop 语境） |

**为什么主 session**: 本 skill 是"对话 + 决策路由"流程, Contract 判定是 Dr Sun 拍板, 必须主 session 跑。代码 / 训练相关 token 重活外派。
