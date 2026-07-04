# Lite3 机器狗导航 DRL 研究项目

> 初始化日期：2026-07-04

本仓库用于在已有机器狗 locomotion（运动控制）基础上发展 navigation（导航）能力。它从 `machine-dog` 迁移了 AI harness、研究纪律、目录约定和基础术语，但不继承旧 walking / parkour 实验结论。

## 当前状态

当前处于规划/调研阶段。尚无 nav Research Contract，禁止启动正式训练，也禁止把旧 walking 结果写成 nav 结果。

## 迁移边界

已迁移：

- `AGENTS.md` / `CLAUDE.md` 项目级 AI 协议。
- `.codex/`、`.claude/`、`.agents/skills/` 的主要工作流配置。
- `.pipeline/` 的长期知识库结构和 Research Contract 模板。
- `bigmemory/` 热区/冷区结构。
- 训练产物、论文 PDF、大文件和敏感文件的 `.gitignore` 规则。

未迁移：

- 旧 `artifacts/` 大体积实验产物。
- 旧 `.pipeline/contracts/*.md` walking 合同。
- 旧 `.pipeline/experiments/*.md` walking 台账。
- 旧 checkpoint 权重和 TensorBoard 日志。

## 目录结构

```text
machine-dog-nav/
├── 0_trials/                # 探索性脚本、一次性演示、候选可视化
├── 1_survey/                # nav 文献调研和论文库
├── 2_experiment/            # nav 实验代码
│   ├── nav_baselines/       # nav baseline 实现
│   └── source_references/   # walking repo / 外部 repo 的轻量来源索引
├── 3_paper/                 # 论文写作
├── 4_assets/                # 地图、场景、传感器、可视化资产
├── 5_algorithm/             # 算法说明页
├── artifacts/               # 训练/评估产物索引和小型 manifest
├── bigmemory/               # AI 会话记忆
├── docs/                    # 项目文档
├── .pipeline/               # 长期结构化知识库
├── AGENTS.md                # AI agent 协议与硬规则
├── CLAUDE.md                # Claude/Codex 入口
└── requirements.txt         # Python 依赖
```

## 关键入口

| 需求 | 入口 |
|---|---|
| 当前状态 | `bigmemory/热区/状态简报.md` |
| 未关闭决策 | `bigmemory/热区/未关闭决策.md` |
| 近期改动 | `bigmemory/热区/近期改动.md` |
| 术语规范 | `.pipeline/terminology/terminology.md` |
| Research Contract 模板 | `.pipeline/contracts/README.md` |
| walking 基础边界 | `docs/walking_base_handoff.md` |

## 第一阶段目标

1. 梳理 nav 任务定义：目标点导航、局部避障、地图输入、传感器输入、评估指标。
2. 建立文献上下文：quadruped navigation、legged navigation、terrain-aware navigation、sim-to-real。
3. 起草第一个 nav Research Contract，明确 hypothesis、success signal、failure signal。
4. 再决定是否复用 `machine-dog` 的 walking policy 作为冻结 base policy。
