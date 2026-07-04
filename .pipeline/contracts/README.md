# Research Contracts

实验前的预注册承诺。一旦提交并被 Dr Sun 批准，禁止原地修改。需修改则新建 v2，并在文件头写明变更原因。

## 当前状态

本仓库尚无 approved nav Contract。正式训练、远端长跑和论文 claim 都必须等待第一个 nav Contract 达到 `approved` 或 `frozen`。

## 模板

~~~yaml
---
version: v1
date: YYYY-MM-DD
status: draft
origin: <ai_only|ai+web|human>
reviewed: false
baseline: <baseline name or none>
---
~~~

### status 三态

- `draft`：草拟中，可继续修改。
- `approved`：Dr Sun 审阅通过，可作为实验依据。
- `frozen`：已进入执行或已被论文/评审引用，只能新建 v2。

~~~markdown
# [实验主题] Research Contract

## Research Question
[这个 nav 实验要回答什么问题]

## Hypothesis
[明确的假设陈述]

## Method
[方法描述，说明 walking base policy 是否冻结、微调或不用]

## Inputs and Outputs
- Inputs:
- Outputs:

## Success Signals
- Signal 1: [具体指标 + 阈值]
- Signal 2:

## Failure Signals（独立定义，不是 success 的反面）
- Signal 1: [具体失败条件]
- Signal 2:

## Ablation Plan
| 实验 | 预期结果 | 判定标准 |
|---|---|---|
| ... | ... | ... |

## Hyperparameters
[锁定的超参列表]

## Data / Terrain Split
[训练/验证/测试场景划分]

## Evidence To Archive
- code commit:
- config:
- stdout/stderr log:
- checkpoint:
- evaluation video:
- metrics:
~~~
