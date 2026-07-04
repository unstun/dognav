---
name: evidence-first-research-iteration
description: |-
  科研实验后的证据优先迭代流程。用于实验、训练、评估、消融或分析结果出来后，先记录事实、核验证据、审计反证，再给出下一轮最小实验建议；当实验形成算法版本更新、候选版本、accepted baseline 或 rejected 版本时，同步生成或更新 5_algorithm/{version}/index.html 版本说明页；普通模式需人工批准，/goal 模式需预授权或多 subagent 投票，防止 AI 基于浅层依据自信修改。适用于 ML、机器人、生物信息、论文实验等科研项目。
argument-hint: "[实验结果或失败现象]"
user-invocable: true
context: inline
---

# Evidence-First Research Iteration

用于一次实验或分析结束后、下一轮修改开始前。目标是把结果变成可复用知识，并判断 AI 是否有资格提出下一步。

本 skill 不运行实验，不改代码，不改 Contract。训练行为、算法、评估规则或数据处理修改，需要先通过本流程，再进入对应的证据检索或实验执行流程。

## 核心规则

先写事实，再写解释。先核验证据，再给建议。证据没有核验，不能支撑修改。

AI 只能给“资格建议”，不能自己批准研究修改。普通模式由 Dr Sun 批准；`/goal` 模式由 goal/Contract/Runbook 预授权，或由 3 个只读 subagent 投票替代过程中的人工确认。

## 1. 识别版本更新

如果实验分析触发以下任一情况，必须同步维护算法版本页：

- 新增算法版本、候选小版本或分支版本
- 更新已有版本的状态、证据、判定或局限
- 产生 accepted baseline、rejected 版本或明确的 draft/screening 版本
- 修改 reward、observation、estimator、control loop、action/executor、terrain/curriculum、PPO、evaluation gate 中任一算法层面的内容

版本页位置固定为：

```text
5_algorithm/{version}/index.html
```

优先使用 `5_algorithm/<nav_version>/index.html` 作为母版。小版本页面可以继承母版，只在顶部新增“本版差异、证据、判定、边界”；accepted baseline 需要扩展为完整算法说明页。

版本页只解释“该算法版本是什么”。正式实验事实仍写入 `.pipeline/experiments/`，预注册依据仍以 `.pipeline/contracts/` 为准。详细栏目与生成规则见 [references/algorithm-version-html.md](references/algorithm-version-html.md)。

## 2. 记录实验事实

```text
实验：
预注册依据/Contract：
Contract 状态：
运行记录：
基线：
本轮改动：
保持不变：
训练/分析设置：
评估设置：
success signal：
failure signal：
原始指标：
可视化/日志：
异常：
```

如果任务要求预注册，但缺少 Contract、运行记录、success signal 或 failure signal，只能给出 `insufficient evidence` 和补记录计划。

## 3. 核验证据

```text
A 级：本项目实验数据、日志、评估指标、视频、人工观察
B 级：本项目源码、配置、脚本、台账、运行环境记录
C 级：外部主要证据，如论文、官方代码、官方文档、已检出的仓库
D 级：AI 推测、类比、经验判断、未核验记忆
```

每条 A/B/C 证据必须写：

```text
等级：
内容：
已核验：是/否
来源：文件位置:行号 / URL / 命令输出 / 实验台账位置
```

未核验的一律降为 D 级。D 级只能提出候选假设，不能支撑修改。

训练行为、算法、奖励、课程、数据处理、评估规则修改，至少需要 A/B/C 中两类已核验证据。A/B/C 互相矛盾时，先写矛盾，不给修改建议。

## 4. 写候选假设

写 1-3 个候选解释。每个解释必须说明机制，不能只重复指标。

```text
H1：
机制：
支持证据：
反对证据：
缺失证据：
什么结果会证明 H1 错：
证据等级：
置信度：low / medium / high
```

好例子：`command curriculum 起点过低，训练早期大量命令被清零，策略学成低速保守行为。`

坏例子：`reward 不好。`

如果写不出“什么结果会证明当前判断错了”，停止给修改建议。

## 5. 审计下一步资格

```text
准备建议什么：
是否只改一个主要因素：
证据是否覆盖当前项目结果：
证据是否覆盖代码/配置机制：
证据是否有外部来源或历史实验支持：
反证是否足够严重：
能否被下一轮实验证伪：
资格建议：可提议 / 只能补证据 / 暂停
```

“可提议”只表示可以把下一轮实验拿去审批，不表示已经可以改代码或开训。

## 6. 设计下一轮最小实验

下一轮只回答一个问题，只改一个主要因素。

```text
问题：
假设：
只改：
不改：
基线：
评估套件：
预期结果：
如果结果 A，说明：
如果结果 B，说明：
如果结果 C，说明：
暂缓修改：
```

多因素修改只能作为后续组合实验，不能作为下一轮归因实验。

## 7. 决策授权

```text
human-approved：普通模式下，Dr Sun 已明确批准。
goal-preauthorized：/goal、approved/frozen Contract 或 Runbook 已写明该分支。
agent-voted：/goal 范围内的新最小实验，经 3 个只读 subagent 全票通过，并且至少 1 个 subagent 独立复核关键来源。
needs-human-review：超出授权、改变研究设计、投票未通过或任一 agent 要求人审。
blocked-by-evidence：证据不足，只能补证据或补诊断。
```

普通模式下，只有 `human-approved` 才能继续修改或训练。

`/goal` 模式下，只有 `goal-preauthorized` 或 `agent-voted` 才能继续。`/goal` 授权的是执行，不是让单个 AI 自己扩大研究设计。

### /goal 多 subagent 投票

当 `/goal` 中未逐条写明下一轮实验，但候选动作仍在 goal 总范围内时，启动 3 个只读 subagent。默认不指定模型，让 subagent 继承主会话模型；不要主动降级。平台支持同能力档位异构模型时，至少 1 个 subagent 使用异构模型；无法异构时记录为 `same-model-vote`，不得称为独立认知制衡。

每个 subagent 独立回答：

```text
vote：approve / reject / needs-human
证据是否已核验：
独立复核的关键来源：
是否只改一个主要因素：
是否仍在 goal 范围内：
是否改变 Contract / success / failure / evaluation suite：
主要顾虑：
```

至少 1 个 subagent 必须独立打开 1 条以上关键来源，核对文件、行号和内容。没有独立复核来源时，投票无效，状态为 `needs-human-review` 或 `blocked-by-evidence`。

投票规则：

```text
3 approve 且满足独立复核：允许继续，记录投票。
任意 reject：暂停，等 Dr Sun。
任意 needs-human：暂停，等 Dr Sun。
```

主会话只能汇总投票，不能把 reject 或 needs-human 改写成 approve。主会话不同意投票时，再开一轮只读复审或暂停。

## 8. 两层判定

分开写实验判定和机制解释，避免把 Contract 失败洗成“证据不足”。

```text
Contract 判定：success / failure / partial / not-applicable
机制解释判定：explained / contradicted / insufficient evidence
```

Contract 判定以预注册信号为准。机制解释只说明是否看懂原因。

## 9. 归档草稿

```text
实验：
事实：
证据核验：
Contract 判定：
机制解释判定：
学到的东西：
被否定的解释：
仍缺的证据：
下一轮最小实验：
决策授权：
不要重复：
算法版本 HTML：
应写入位置：
```

归档重点是未来可复用判断，不是流水账。

## 停止条件

出现以下情况时，停止给修改建议，只给补证据计划：

- 没有基线，或评估套件相对基线已变化且未说明
- 只看到视频，没有指标或日志
- 只有 D 级证据
- A/B/C 证据未核验
- 下一轮需要同时改多个主要因素
- success/failure 信号需要改写
- 任务要求预注册，但缺少 Contract、运行记录或预注册判定信号
- 外部资料未核验到原文、源码或官方文档
- 当前证据无法说明“什么结果会打脸这个判断”
- 普通模式缺少 `human-approved`
- `/goal` 模式缺少 `goal-preauthorized` 或 `agent-voted`

## 和其它 skill 的关系

- `experiment-loop`：负责 Contract、运行、台账和逐轮确认。
- `evidence-grounded-training-modification`：负责训练行为修改前找源码、论文和本地证据。
- 本 skill：负责实验后把事实、证据核验、授权方式、下一轮最小实验和算法版本 HTML 分清楚。

详细例子见 [references/examples.md](references/examples.md)。
