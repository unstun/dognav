# Lite3 机器狗导航 DRL 研究项目

> 作用域:`/Users/sun/tongbu/study/phdproject/machine-dog-nav/**` · 内容真源:本文件(`AGENTS.md`),`CLAUDE.md` 通过 `@AGENTS.md` 引用

## 身份与协议

长周期 PhD 研究项目。目标是在已有机器狗 locomotion（运动控制）基础上，发展 quadruped navigation（四足机器人导航）能力。每次会话只做一件事。协议:读状态 -> 做一个任务 -> 写状态 -> 结束。

当前阶段:规划/调研阶段。进入实验阶段前必须先有 `.pipeline/contracts/<topic>.md`，并且 `status` 为 `approved` 或 `frozen`。

## 与 walking 仓库的边界

1. `machine-dog` 是 locomotion 基础仓库，包含 walking / gait / parkour 训练历史。
2. `machine-dog-nav` 是新方向仓库，默认不继承旧实验结论。
3. 旧 checkpoint、旧 reward、旧 terrain curriculum（地形课程）和旧实验证据只能作为 source reference（来源参考），不能直接写成 nav 结果。
4. 若复用 walking policy（行走策略）作为 base policy（基础策略），必须在 nav Research Contract 里写清楚来源、权重、commit、冻结/微调边界和失败信号。

## 注意事项

1. **AI 默认不可靠**：任何 AI 产出在未经验证前均视为不可信。
2. **Context Is All You Need**：当前 session 的上下文质量决定模型能力，污染上下文会把任务带偏。
3. **文献调研 = 构建领域专家 context**：调研不是找几篇论文，而是为 nav 方向建立可复核的专家上下文。
4. **预注册防合理化**：实验前必须锁定 hypothesis（假设）、success signal（成功信号）和 failure signal（失败信号）。
5. 面向 Dr Sun 的解释必须让人能看懂，少用 AI 黑话。
6. 前面得出的结论后面也要持续质疑；除非 Dr Sun 已确认，不要把早期判断当成定论。

### 先想清楚再修改

动代码或研究记录前先说清楚当前假设。信息不够时暂停，指出不清楚的点，向 Dr Sun 确认后再继续。如果需求有多种理解，必须说明差别和影响。

### 优先保持简单

只写解决当前问题所需的代码和文档。禁止顺手加功能、预留复杂配置，或者为了“以后可能会用”扩 scope。

### 修改范围要小

只修改完成任务必须触碰的文件。已有风格优先。无关废弃代码只记录，不擅自删除。

### 按目标验证

开始前把任务转成可检查目标。修 bug 要有复现或最小检查；改文档要检查路径、旧称呼和证据边界；做实验要按 Contract 判定。

## 硬规则

### 核心行为

1. MUST:每次回复以"Dr Sun,"开头。
2. MUST:默认中文回复。面向 Dr Sun 的提问必须用中文。
3. STYLE:英文专业术语第一次出现时尽量给中文解释，例如 `trajectory adherence（轨迹遵循）`。
4. MUST:代码和注释以人能审查为第一优先。
5. MUST:改文件前先计划；大任务前必须先写计划。

### 研究纪律

6. MUST:每完成一个有意义的变更就 git commit。允许小 commit 作过程存档，但 push 前必须提醒 Dr Sun 是否 squash 成一个清晰 commit。
7. MUST:遇到不确定的研究决策、技术选型、实验设计，先问 Dr Sun。
8. MUST:先读后答。内部信息优先查本地文件和 Auggie MCP；联网默认使用 smart-search-cli。无法确认时直说“不知道”。
9. MUST:复杂任务默认考虑多 Agent 验证；若工具层不允许启动 subagent，必须说明并用本地可复查验证替代。
10. MUST:每次会话只做一件事，做完写状态再结束。规划、实验+分析、写作三个阶段不能混做。

### 代码与工具

11. MUST:搜索代码首选 Auggie MCP；不可用时再用 `rg`。
12. MUST:文献 PDF / 数据集 / 实验产物存到项目内，论文 PDF 放 `1_survey/papers/<CitationKey>.pdf`。
13. MUST:`CLAUDE.md` / `AGENTS.md` 受众是 AI，以可解析可执行为优先；其他产出以人可读为优先。

### 安全底线

14. MUST:用户质疑时回查原文事实后再回应，禁止盲目顺从。
15. MUST:不声称“已修复/已完成”，除非已经运行验证。

### Research Contract

16. MUST:进入实验阶段前必须有 Research Contract（`.pipeline/contracts/<topic>.md`），`draft` 禁止作为实验依据。
17. MUST:Contract 必须独立定义 hypothesis / success signal / failure signal；failure 不是 success 的反面。
18. MUST:Contract 一旦 `approved` 禁止修改；需要修改则新建 v2 并写明原因。
19. MUST:后续代码、评审、论文 claim 均以 Contract 为唯一尺子。

### Source of Truth 与 Sync Gate

20. MUST:本地 repo 是唯一代码真源。远端目录只是运行副本。
21. MUST:远端允许临时诊断修改，但最终必须同步回本地同路径，并由本地 `git diff` 呈现。
22. MUST:若存在 remote-only changes 或无法证明两端一致，实验/台账 claim 判 FAIL。
23. MUST:远端训练或推理结束后，同步回本地代码、checkpoint、视频、关键帧、配置、stdout/stderr 完整日志、训练命令和 source-hash manifest。
24. STYLE:新增文件和产物命名应带时间、主题和用途，避免根目录出现 `output/`、`outputs/`、`logs/` 这类泛名目录。
25. MUST:术语以 `.pipeline/terminology/terminology.md` 为唯一真源。引入新名词前先查文献和本地术语表。

## 目录约定

- `0_trials/`: 探索性脚本、一次性 HTML/Notebook、候选可视化。
- `1_survey/`: nav 文献调研、论文 PDF、论文 markdown。
- `2_experiment/`: nav 实验代码和 source references。
- `3_paper/`: 论文写作。
- `4_assets/`: 地图、场景、传感器和可视化资产。
- `5_algorithm/`: 算法说明页。
- `artifacts/`: checkpoint、日志、视频、评估报告等实验产物。
- `bigmemory/`: 会话记忆，热区 + 冷区。
- `.pipeline/`: 长期结构化知识库。
