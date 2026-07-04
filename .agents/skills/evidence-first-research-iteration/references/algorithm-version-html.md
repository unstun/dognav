# Algorithm Version HTML

用于在算法版本更新时生成或更新 `5_algorithm/{version}/index.html`。本文件只规定版本页结构；实验事实以 `.pipeline/experiments/` 为准，预注册依据以 `.pipeline/contracts/` 为准。

## 触发条件

出现以下情况时，必须维护版本页：

- 新增算法版本、候选小版本或分支版本
- 版本状态变化：`draft`、`screening`、`accepted`、`rejected`
- reward、observation、estimator、control loop、action/executor、terrain/curriculum、PPO、evaluation gate 发生算法层面的变化
- 实验后形成 accepted baseline 或明确失败版本

## 文件位置

```text
5_algorithm/{version}/index.html
```

例如：

```text
5_algorithm/wave_c_v9j/index.html
```

如果新增页面，也要检查以下入口是否需要同步：

```text
5_algorithm/index.html
5_algorithm/README.md
5_algorithm/wave_c_v9/index.html
```

## 母版

优先使用：

```text
5_algorithm/wave_c_v8i/index.html
```

小版本页面可以继承母版结构。继承母版时，页面顶部必须写清楚：

```text
本页只有“本版差异”块是当前版本新增内容；
后续架构正文来自哪个母版；
当前版本继承了哪些算法底座；
哪些内容只是设计或 draft，尚未训练验证。
```

accepted baseline 需要扩展为完整算法说明页，覆盖观测、估计器、训练、控制循环、动作执行器、奖励、地形课程、PPO、版本来源和局限。

## 内容覆盖

版本页可以采用叙述式结构，不要求逐字使用以下字段名，但内容必须覆盖：

```text
版本名：
版本状态：
父版本：
本版目标：
本版改动：
Contract 来源：
实验台账来源：
源码来源：
外部参考：
实验判定：
当前局限：
禁止倒写成事实的内容：
生成位置：
```

`源码来源` 要尽量写到文件和行号。外部参考只能作为设计启发，除非已经核验到原始论文、官方代码或官方文档。

## 本版差异块

小版本页面顶部必须有 `version-delta` 区块。推荐内容：

```text
状态标签：draft / screening / accepted / rejected
父版本：从哪个版本继承
只改：本轮唯一主要因素
不改：保持不变的算法部分
证据：Contract、实验台账、源码、artifact
判定：success / failure / partial / not-applicable
边界：哪些说法不能写成已验证事实
```

如果版本仍是 `draft`，页面必须显式写出“尚未训练”或等价说明，避免后续误读。

## 页面边界

版本页用于解释算法版本，不能替代以下文件：

```text
.pipeline/contracts/<topic>.md
.pipeline/experiments/<date>/<topic>.md
artifacts/<run-or-analysis>/
```

禁止把以下内容写成已验证事实：

- draft Contract 中尚未训练的设计
- 只有视频观察、缺少指标和日志的判断
- 只有 AI 推测、缺少 A/B/C 已核验证据的解释
- 外部项目中的机制，未经本项目实验或源码确认就写成当前版本已有能力

## 检查项

提交前检查：

```text
HTML 能打开
页面顶部有版本状态和父版本
本版差异与继承内容分开
Contract、实验台账、源码来源齐全
draft / screening / accepted / rejected 状态没有混写
5_algorithm/index.html、5_algorithm/README.md、系列入口页按需更新
```
