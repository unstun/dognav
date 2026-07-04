# Walking Base Handoff

`/Users/sun/tongbu/study/phdproject/machine-dog` 是 walking / gait / parkour 方向的基础仓库。`machine-dog-nav` 可以引用它，但不能把旧结果自动升级为 nav 证据。

## 可复用内容

- AI harness 规则：先计划、Research Contract、Sync Gate、术语真源、热区状态。
- 目录约定：`0_trials/`、`1_survey/`、`2_experiment/`、`.pipeline/`、`artifacts/`。
- 可能的 base policy：只有在 nav Contract 写清权重、commit 和冻结/微调边界后才能使用。

## 不可直接复用为 nav 证据

- walking / gait / parkour 的旧 success signal。
- old `wave_c_*`、`v9j*`、`PIE*` 合同和台账。
- 旧 checkpoint 的性能结论。
- 旧 terrain curriculum 的失败/成功解释。

## 第一个 nav Contract 必须回答

1. Nav 任务到底是什么：point-goal、waypoint following、map-based navigation、local obstacle avoidance，还是组合任务。
2. 输入是什么：proprioception、depth、height map、local map、goal vector、command velocity。
3. 输出是什么：velocity command、foothold target、residual action，还是 end-to-end joint action。
4. walking policy 是冻结底层控制器、可微调策略，还是只作为比较 baseline。
5. 成功和失败怎么独立定义。
