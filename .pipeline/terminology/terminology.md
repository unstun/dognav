# 术语规范

| 中文 | 英文 | 缩写 | 备注 |
|------|------|------|------|
| 深度强化学习 | Deep Reinforcement Learning | DRL | |
| 四足机器人 | Quadruped Robot | — | 不用"四足机器狗" |
| 机器狗导航 | Quadruped Navigation / Legged Robot Navigation | — | 本仓库主方向；具体任务需在 Contract 中定义为 point-goal、waypoint、mapless 或 map-based navigation |
| 目标点导航 | Point-Goal Navigation | — | 机器人根据相对目标向量或目标位置到达指定区域 |
| 路标跟踪 | Waypoint Following | — | 机器人按一串 waypoint 逐段前进 |
| 局部避障 | Local Obstacle Avoidance | — | 在局部感知范围内绕开障碍，不等同于全局路径规划 |
| 无图导航 | Mapless Navigation | — | 不使用显式地图，通常依赖当前观测和目标表示 |
| 地图导航 | Map-Based Navigation | — | 使用局部地图、高度图或占据栅格等显式空间表示 |
| 森林跑酷 | Forest Parkour | — | 来自 walking 基础仓库的旧方向；在本仓库只能作为背景或 source reference |
| 近端策略优化 | Proximal Policy Optimization | PPO | |
| 软演员-评论家 | Soft Actor-Critic | SAC | |
| 课程学习 | Curriculum Learning | CL | |
| 域随机化 | Domain Randomization | DR | |
| 本体感知 | Proprioception | — | |
| 高度图 | Height Map / Heightfield | — | |
| 仿真到现实 | Sim-to-Real / Sim2Real | — | |
| 自由度 | Degrees of Freedom | DOF | |
| 地形感知 | Terrain-Aware | — | |
| 步态 | Gait | — | |
| 运动控制 | Locomotion Control | — | |
| 发送力矩目标 | Effort Target | — | Isaac Lab 训练诊断中由策略动作经控制律生成并发送给关节执行器的力矩目标；不要写成真实电机反馈扭矩 |
| 模态迁移蒸馏 | Modality Shift Distillation | — | 教师策略用特权感知（如高度图），学生策略用机载传感器（如深度相机）；Rudin2025 核心范式 |
| 三段观测流水线 | Expert/Student/Critic Obs Pipeline | — | Rudin2025 Table 3 范式：expert obs（含高度图）、student obs（深度相机）、critic obs（完整）三组输入分别喂不同网络 |
| 预训练先跑 | Pretrained-Play-First | — | 训练前用预训练 checkpoint 跑 Play 模式验证代码链路；CAI23sbP 提供 Teacher+Student 预训练权重；防止代码错误在正式训练中浪费算力 |
| 失败时间 / 距失败步数 | time-to-failure | ttf | FMC-Parkour 预警头输出的标量，量化"当前状态再走几步会发生跌倒/失控"；与策略联合端到端训练；理论基础见 safety value function V_safe(s) |
| 安全价值函数 | safety value function | V_safe(s) | 满足修改版 Bellman 方程的价值函数，表示从当前状态出发能够保持安全的最优值；理论先例：Fisac2019BridgingHJ、Yu2022RCRL、Massiani2023SafeValueFunctions；FMC 中 ttf 头是其离散化近似 |
| 危险感嵌入 | danger embedding | e | FMC-Parkour 预警头的内部隐层表示，编码当前状态的危险程度；作为额外输入反馈给行走策略（actor），实现策略与预警头的联合端到端训练 |
| 危险预感器 | danger predictor | — | 危险感 v3 核心模块之一；消费本体感知观测，输出对当前状态危险程度的读数（标量或向量），供出手强度网络决策 |
| 防御反射 | defensive reflex | — | 危险感 v3 核心模块之一；基于危险读数生成对主策略动作的残差修正量，用于在高危时刻使动作偏向保守 |
| 残差修正量 | residual correction | Δa | 防御反射输出的动作偏置向量；与主策略输出相加得到最终执行动作；被出手系数 g 打折以控制实际介入强度 |
| 出手强度网络 | intervention intensity network | g_φ | 参数为 φ 的独立小网络；输入最近若干步危险读数，输出 0~1 的出手系数；是危险感 v3"门控"的具体实现；由 Dr Sun 2026-06-12 拍板 |
| 出手系数 | intervention coefficient | g | 出手强度网络的输出标量，取值 0~1；对防御反射残差修正量打折（最终修正 = g × Δa）；g=0 表示不出手，g=1 表示全力介入 |
| 出手费 | intervention cost | — | 奖励函数中的小额惩罚项；与出手系数大小和持续时长正相关；迫使出手强度网络在无危险时把 g 压近 0，防止其偷懒学成恒 1；由 Dr Sun 2026-06-12 拍板 |
| 跑酷障碍地形 | parkour terrains / obstacle course | — | 跑酷训练用的离散障碍地形总称，类型沿 PIE 原文：间隙 gap、台阶 step、跨栏 hurdle、楼梯 stairs，另有垫脚石 stepping stones（ANYmal Parkour）；禁用自造词"积木地形/积木场景/积木化地形"；依据 Luo2024_PIE 第 164 行，Dr Sun 2026-06-12 确认 |
| 地形课程 | terrain curriculum | — | 地形难度由易到难逐级递进的训练机制（课程学习在地形上的具体应用）；依据 PIE/Rudin2022；禁用自造词"积木课程" |
| 地形原点 | terrain origin | — | 由 terrain generator 为每个 `(terrain_level, terrain_type)` cell 记录的世界坐标原点；不要和环境原点混用 |
| 环境原点 | environment origin / env origin | — | Isaac Lab 中 `env.scene.env_origins[env_id]`，实际用于放置机器人的环境坐标原点；PIE5A probe 已证明它必须和 terrain level/type 同步检查 |
| 跑酷起点 | parkour start | — | 机器人在跑酷障碍地形前方的安全出生位置；PIE3/PIE5A reset 会从 terrain origin 沿 x 方向后退到该位置，不能被 terrain curriculum 误当成已经前进 |
| 前向进度 | forward progress | — | 沿任务前进方向计算的进度；parkour terrain curriculum 应优先用从 parkour start 出发的前向进度，而不是到 terrain origin 的 xy 欧氏距离 |
| 基础策略 | base policy | π_base | 残差策略学习中被冻结的底层策略，文献称 frozen base policy；危险感 v3 中即"执行者"（v9j 训练方案所得）；禁用自造词"底座"（指环境时写"仿真环境"） |
