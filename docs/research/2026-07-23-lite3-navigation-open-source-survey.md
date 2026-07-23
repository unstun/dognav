# Lite3 四足机器人自主导航第一轮“文献 + 开源代码 + 可复现性”深度调研

- **项目**：`machine-dog` / `machine-dog-nav`
- **核验日期**：2026-07-23
- **报告性质**：联网调研、源码与文档审计；未执行上游程序
- **当前最高证据状态**：`surveyed`
- **研究边界**：本轮不编写导航框架，不修改 Lite3 运动控制仓库，不训练模型，不控制真机，不把任何候选描述为已复现、已集成或已验证。

## 证据状态与措辞规则

| 状态 | 本报告中的严格定义 |
|---|---|
| `surveyed` | 已检查论文、官方项目页、canonical 仓库、README/文档、许可证、固定 commit，以及部分 issue/release 信息。 |
| `reproduced` | 原始上游命令在指定环境实际运行成功，且保存版本清单、终端日志、rosbag/视频、指标与失败记录。**本轮没有任何候选达到此状态。** |
| `integrated` | 上游能力已经接入 `machine-dog-nav`，并通过明确定义的导航—运动控制接口调用 `machine-dog`。**本轮没有。** |
| `validated` | 预先声明的项目验收测试通过。**本轮没有。** |

论文中的“首次”“SOTA”“优于”等表述，以下若出现均明确标为**作者报告**。公开视频、论文实验、作者演示和第三方 issue 不能替代本项目的 `reproduced` 证据。

---

## 1. 一页式结论

### 1.1 排名与条件化推荐

**第一复现对象：ROS 2 Navigation2（Nav2）。**

理由不是“Nav2 对四足机器人最先进”，而是它最适合建立可审计的第一条导航闭环：

1. 官方提供稳定的 ROS 2 二进制安装、TurtleBot/Gazebo 最小演示、完整配置和插件文档；第一轮 smoke test 不需要训练权重或 CUDA。
2. 规划层和控制层边界明确：`ComputePathToPose/ThroughPoses` 输出 `nav_msgs/Path`，控制器服务器再消费路径并产生 `Twist`/`TwistStamped`。因此可以先复现官方全栈，再单独复现“目标位姿 → 路径”，最后把路径采样成 Lite3 几何航点，而不必立即采用 Nav2 的原控制器。
3. Nav2 支持自定义 planner/controller/costmap/behavior 插件；它适合作为长期实验框架和基线，而不只是一次性 demo。
4. 维护、文档、ROS 发行版和社区问题单均明显优于大多数研究仓库。

**第二候选：ViPlanner。**

它是本轮最清晰的学习型四足局部规划候选。源码中规划器发布 `/viplanner/path`（`nav_msgs/Path`），独立的 `pathFollower` 再将路径转换成默认 `/cmd_vel` 的 `TwistStamped`。这意味着可以保留视觉/语义局部规划器，替换其 follower，将路径转为 Lite3 航点或由项目自有跟踪器执行。主要代价是 ROS 1 Noetic、CUDA/mmcv/Isaac Sim 依赖、相机与机器人高度迁移、数据资产和 checkpoint 环境兼容。

**第三候选：Quad-SDK，条件是博士课题优先研究四足专用的全身规划—足步—控制纵向栈。**

其 2026 年 ROS 2 Jazzy 文档、Gazebo/MuJoCo/Isaac Sim 后端、自定义控制器接口、RRT-Connect 全局身体规划、NMPC 局部身体规划和 Raibert 足步规划具有很高研究价值；但它不是“轻量导航层”。Lite3 不在上游支持列表中，且 HSL/IPOPT、机器人模型、消息、估计与低层控制耦合使替换成本高。它适合在 Nav2 基线之后独立复现，不适合第一条最小闭环。

**FAR Planner 是许可证解决后的条件候选。** 技术上其可见性图路径/waypoint 边界适合外部控制器，依赖和算力也不重；但仓库根目录未找到明确许可证，且官方运行依赖外部 AEDE/`vehicle_simulator`，已有缺包、仿真停滞和真机部署问题单。未取得作者书面授权前，不应把其源码合入 `machine-dog-nav`。

### 1.2 第一阶段是否应采用几何航点

**建议采用，但必须是条件化决策：把“几何航点”定义为 `machine-dog-nav` 与 `machine-dog` 之间的第一研究接口；只有在 Lite3 运动控制器确认原生接受航点或已有可靠航点跟踪器时，才把它作为直接执行接口。**

推荐的第一版语义是：

```text
WaypointCommand
  frame_id: base_link 或 odom（二选一并固定）
  stamp: 生成时间
  position: x, y；可选 z
  heading: 可选 yaw / heading_mode
  tolerance: 到达容差
  sequence_id: 序号
  validity_horizon: 失效期限
  behavior: replace / append / cancel / stop
```

几何航点适合第一阶段的原因：

- 将导航频率与关节控制频率解耦；导航层只负责“下一步去哪里”，低层策略负责“怎样走过去”。
- 可由 Nav2、FAR、ViPlanner、VLA/VLN 或人工脚本统一产生，便于替换上游算法。
- 比高频速度流更容易记录、重放、可视化、做坐标系单元测试和故障归因。
- 给强化学习运动控制器保留局部地形适应、步态选择和恢复动作的空间。
- 能自然演化为“全局路径 → 局部路径/短轨迹 → 航点 → RL locomotion”的分层结构。

但它不是安全保证。单个航点通常不含时间参数、曲率、速度包络、碰撞余量、支撑面、落足可行性和动态障碍信息；可能发生切角、追逐过期目标、坐标系错误、在缝隙/边缘/障碍内部生成目标，或要求低层执行不可达运动。Skill-Nav 论文也明确报告其航点可能落在缝隙或箱体边缘；该系统目前没有可检查的公开 canonical 代码，只能作为接口设计参考，不能作为第一复现仓库。

**若 `machine-dog` 实际只接受高频 `Twist`，则不要为了形式强行采用航点。** 第一条真闭环应先使用“Nav2/局部规划器 → 速度安全适配器 → `machine-dog`”，同时在 `machine-dog-nav` 内保留路径/航点抽象；待运动控制器具备航点跟踪能力后再切换。Lite3 厂商公开 ROS 2 桥接当前订阅 `/cmd_vel`，不能据此推断项目自研 RL 控制器已经支持航点。

### 1.3 当前最大未知条件与阻塞项

1. **`machine-dog` 的真实执行接口未知**：接受 `Twist`、相对航点、全局目标位姿、短轨迹，还是策略特定 observation/action；是否支持队列、抢占、取消、到达反馈。
2. **坐标系契约未知**：`map → odom → base_link` 是否完整；状态估计的 frame、时间戳、漂移、协方差、更新率和外参尚未确认。
3. **实时与安全契约未知**：指令频率、网络/进程延迟上限、watchdog、急停、失联、过期命令、跌倒与恢复行为尚未确认。
4. **ROS 代际冲突**：Lite3 官方 ROS 2 示例面向 Foxy/Ubuntu 20.04；本报告首选的现代研究基线是 Jazzy/Ubuntu 24.04。是否升级、容器隔离、DDS 跨机通信或建立协议桥，需要在集成前决定。
5. **机器人能力包络未知**：最大速度/加速度/角速度，横向能力、最小转弯行为、坡度/台阶/缝隙/摩擦边界、相机和 LiDAR 配置均会改变 planner 参数。
6. **许可证阻塞**：FAR、TARE、Agile Navigation 根目录未找到明确代码许可证；可查看不等于可复制、修改或分发。
7. **尚无本项目运行证据**：本轮所有选择均为 `surveyed`，不是 `reproduced`。

---

## 2. 技术路线图

### 2.1 分层边界

```text
任务/语言/目标
      │
      ▼
VLA/VLN 高层语义规划 ──► 结构化语义子目标 / metric subgoal / 行为约束
      │
      ▼
全局规划：地图 + 当前位姿 + 目标 ──► 全局几何路径 nav_msgs/Path
      │
      ▼
局部规划与避障：局部地图 + 路径 + 状态 ──► 局部路径 / 短轨迹 / 安全速度
      ▲
      │
地形可通行性：点云/深度/RGB/本体感觉 ──► 高程、风险、语义或速度代价层
      │
      ▼
导航—运动控制桥：路径/轨迹 ──► 几何航点、目标位姿或速度指令
      │
      ▼
Lite3 RL locomotion：命令 + 观测 ──► 关节目标/力矩/底层 SDK
      │
      └────────────── 状态估计、接触、故障、进度反馈 ──────────────┘
```

### 2.2 各层输入、输出和责任边界

| 层 | 典型输入 | 典型输出 | 本层负责 | 本层不应被误认为负责 |
|---|---|---|---|---|
| 感知 | RGB、深度、点云、2D/3D LiDAR、IMU、关节/接触 | `Image`、`PointCloud2`、`LaserScan`、语义 mask、障碍物 | 标定、同步、滤波、检测/分割、地面或障碍提取 | 不直接保证全局可达或动态稳定 |
| 定位/状态估计 | IMU、轮/腿里程计、视觉/LiDAR、关节状态 | `map→odom→base_link`、pose、twist、协方差 | 提供连续、带时间戳的机器人状态 | 不负责选路或执行步态 |
| 建图 | 位姿 + scan/point cloud/depth/semantics | 2D occupancy、3D point/voxel map、elevation/grid map、scene graph | 环境表示、更新与持久化 | 地图可见不等于机器人可通行 |
| 全局规划 | 当前位姿、目标、全局地图/图、代价 | `nav_msgs/Path`、route graph | 长距离拓扑或几何可达性、路径长度/代价 | 通常不保证实时跟踪、足步可行或动态避障 |
| 局部规划与避障 | 全局路径、局部地图、机器人状态、动态障碍 | 局部路径、短时轨迹、`Twist` | 实时避障、跟踪、局部恢复、速度约束 | 不应承担关节级稳定控制 |
| 地形可通行性 | 高程、点云、RGB/语义、本体感觉、历史通过结果 | traversability/risk/speed layer | 把“障碍”扩展为机器人特定风险和偏好 | 不是完整目标导航器；仍需 planner |
| 导航—运动控制桥 | path/trajectory/goal + 当前状态 | waypoint、pose、velocity、skill command | 坐标变换、采样、限幅、失效、抢占、反馈映射 | 不应隐藏碰撞检查或绕过安全监控 |
| 运动控制 | waypoint/velocity/trajectory + proprioception/exteroception | 关节位置/速度/力矩、步态、接触 | 动态稳定、地形适应、执行和恢复 | 不应自行承担长距离语义决策 |
| VLA/VLN | 语言、图像/视频、语义地图、历史 | 语言中间动作、地标、metric subgoal、任务约束 | 长时序语义推理与目标分解 | 不应未经验证直接输出关节动作或绕过几何安全层 |

### 2.3 候选技术按层归类

| 方向 | 首选基座 | 次选/研究候选 | 说明 |
|---|---|---|---|
| 几何导航与局部避障 | Nav2 | FAR Planner；Agile Navigation | Nav2 最适合作为长期基线；FAR 适合 3D/未知环境 route 研究但有许可证和 AEDE 阻塞；Agile 更偏四足短轨迹和 NMPC。 |
| 2D 激光建图与定位 | SLAM Toolbox + Nav2 | RTAB-Map ROS 的 2D/ICP 配置 | SLAM Toolbox 边界最清晰；需注意特定版本的问题单与地图保存安全。 |
| RGB-D/双目/3D LiDAR SLAM | RTAB-Map ROS | 独立 LiDAR-inertial odometry + Nav2/高程图 | RTAB-Map 支持多模态，但性能与参数组合较多，必须按传感器单独验收。 |
| 视觉局部导航 | ViPlanner | Habitat-Lab/VLN-CE（评测）；NaVILA（高层） | ViPlanner直接输出路径；Habitat 更适合离线基准；NaVILA不是第一阶段几何栈。 |
| 粗糙地形与可通行性 | Elevation Mapping CuPy + 经典/自定义 cost layer | WVN；LeSTA；ViPlanner | 先把可通行性作为代价层，不要把估计器误称为完整导航器。 |
| 学习型局部规划器 | ViPlanner | WVN/LeSTA + Nav2 MPPI 或自定义 planner | WVN/LeSTA输出风险，不直接输出完整路径；Nav2 MPPI 是采样式模型预测控制器，不是学习型模型。 |
| 四足专用纵向规划 | Quad-SDK | Agile Navigation | 可研究 body trajectory、footstep 和控制耦合；对 Lite3 的机器人模型与底层接口改造大。 |
| 探索 | TARE | FAR + frontier/route 层；WildOS | TARE目标是自主探索，不是给定目标点的最小导航闭环。 |
| VLA/VLN 高层规划 | NaVILA | WildOS；BehAV；Habitat/VLN-CE | NaVILA发布较完整但环境重；WildOS强调语义图和几何安全；BehAV当前仓库编排不足。 |
| VLA → planner → RL locomotion | NaVILA 高层或 WildOS/BehAV 语义层 + Nav2/ViPlanner + `machine-dog` | Skill-Nav仅作架构参考 | 推荐让 VLA 输出受约束的 metric subgoal/行为代价，再由 planner 和 RL locomotion 执行。 |

---
## 3. 15 个候选全景表

### 3.1 版本、论文、许可证与维护

> “固定 commit”是 2026-07-23 的源码审计快照，不代表该 commit 已在本项目运行。对 Nav2 第一轮 smoke test，建议使用 ROS 发行版二进制并另外锁定 apt 包版本；`main` SHA 仅用于审计当前上游状态。

| ID | 项目与原始论文 | Canonical 仓库 | 许可证 | 默认分支与固定 commit（2026-07-23） | Release、维护与重要未解决问题 | 状态 |
|---|---|---|---|---|---|---|
| C01 | **Navigation2 / Nav2**；[The Marathon 2: A Navigation System](https://arxiv.org/abs/2003.00368) | [ros-navigation/navigation2](https://github.com/ros-navigation/navigation2)；[官方文档](https://docs.nav2.org/) | 按包混合：Apache-2.0、BSD-3-Clause、LGPL-2.1-or-later；复用时须逐包核验 | `main`；[`db906947171abe170c25181347be9bc7bcbc1a75`](https://github.com/ros-navigation/navigation2/commit/db906947171abe170c25181347be9bc7bcbc1a75) | **活跃**；HEAD 接近核验日。官方为 Humble/Jazzy/Kilted 等提供稳定二进制与 release/nightly 容器。当前 issue 涉及新 ROS 发行版跟踪、MPPI/路径重发和动态 footprint 等；属于持续演进而非无人维护。 | `surveyed` |
| C02 | **SLAM Toolbox**；[SLAM Toolbox: SLAM for the Dynamic World](https://joss.theoj.org/papers/10.21105/joss.02783) | [SteveMacenski/slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) | LGPL-2.1 | `ros2`；[`eee0cd5e4a161bb10f8334b5420c93876b31ca99`](https://github.com/SteveMacenski/slam_toolbox/commit/eee0cd5e4a161bb10f8334b5420c93876b31ca99) | **活跃**；该 HEAD 于 2026-07-22 修复 RViz 初始位姿 frame 处理。通过 ROS 发行版发布。需关注 [#662 最大量程清除](https://github.com/SteveMacenski/slam_toolbox/issues/662)、[#827 重复加载地图内存增长](https://github.com/SteveMacenski/slam_toolbox/issues/827)、[#867 Humble `save_map` 安全报告](https://github.com/SteveMacenski/slam_toolbox/issues/867)。 | `surveyed` |
| C03 | **RTAB-Map ROS**；[RTAB-Map as an open-source lidar and visual SLAM library](https://doi.org/10.1002/rob.21831) | [introlab/rtabmap_ros](https://github.com/introlab/rtabmap_ros)；[RTAB-Map](https://github.com/introlab/rtabmap) | BSD-3-Clause 风格 | `ros2`；[`2eef2b3231090f0a5cc2e092fd993166157cdd64`](https://github.com/introlab/rtabmap_ros/commit/2eef2b3231090f0a5cc2e092fd993166157cdd64) | **活跃**；该 HEAD 增加 ROS 2 Lyrical 支持并将包版本推进到 0.23.7。提供 ROS 二进制和多发行版 Docker。需关注 [#1438 Jazzy ICP odometry 频率下降](https://github.com/introlab/rtabmap_ros/issues/1438)、[#1436 D435i 近物体后显示/恢复问题](https://github.com/introlab/rtabmap_ros/issues/1436)、[#1426 地图原点差异](https://github.com/introlab/rtabmap_ros/issues/1426)。 | `surveyed` |
| C04 | **FAR Planner**；[FAR Planner: Fast, Attemptable Route Planner using Dynamic Visibility Update](https://arxiv.org/abs/2110.09460) | [MichaelFYang/far_planner](https://github.com/MichaelFYang/far_planner)；[官方项目页](https://www.cmu-exploration.com/far-planner) | **未找到根目录 LICENSE；代码复用阻塞** | `melodic-noetic`；[`2799b6964c141cacd1c32a14b19bc7abffbe0e52`](https://github.com/MichaelFYang/far_planner/commit/2799b6964c141cacd1c32a14b19bc7abffbe0e52) | **低/稀疏维护**；未找到正式 GitHub Release。重要问题：[缺少 `vehicle_simulator` #17](https://github.com/MichaelFYang/far_planner/issues/17)、[真机部署 #14](https://github.com/MichaelFYang/far_planner/issues/14)、[索引问题 #19](https://github.com/MichaelFYang/far_planner/issues/19)、仿真失败/边界伪影。 | `surveyed` |
| C05 | **TARE Planner**；[TARE: A Hierarchical Framework for Efficiently Exploring Complex 3D Environments](https://www.roboticsproceedings.org/rss17/p018.html)；扩展工作 [Representation granularity enables time-efficient autonomous exploration](https://doi.org/10.1126/scirobotics.adf0970) | [caochao39/tare_planner](https://github.com/caochao39/tare_planner) | **未找到根目录 LICENSE；代码复用阻塞** | `melodic-noetic`；[`44500592b86138257273e0cab264e6a847ccefc7`](https://github.com/caochao39/tare_planner/commit/44500592b86138257273e0cab264e6a847ccefc7) | **低/稀疏维护**；未找到正式 GitHub Release。重要问题：[动态障碍 raytracing 缺口 #21](https://github.com/caochao39/tare_planner/issues/21)、[OR-Tools/GLIBC #28](https://github.com/caochao39/tare_planner/issues/28)、[真机立即结束 #29](https://github.com/caochao39/tare_planner/issues/29)、[缺 `vehicle_simulator` #30](https://github.com/caochao39/tare_planner/issues/30)。 | `surveyed` |
| C06 | **Quad-SDK**；[Quad-SDK: Full Stack Software Framework for Agile Quadrupedal Locomotion](https://robomechanics.github.io/quad-sdk/latest/)（ICRA Legged Robots Workshop 2022） | [robomechanics/quad-sdk](https://github.com/robomechanics/quad-sdk)；[ROS 2 文档](https://robomechanics.github.io/quad-sdk/ros2/) | MIT | `main`；[`50b58ce8f248ff8995270eae3fa0488c91eeddd4`](https://github.com/robomechanics/quad-sdk/commit/50b58ce8f248ff8995270eae3fa0488c91eeddd4) | **活跃**；2026-06 更新 ROS 2 Jazzy 文档和多模拟器流程。未把 GitHub Release 作为主要入口。重要问题：[Jazzy 目标后 local planner 崩溃 #443](https://github.com/robomechanics/quad-sdk/issues/443)、[HSL 新版本导致 setup/NMPC 失败 #425](https://github.com/robomechanics/quad-sdk/issues/425)、[adaptive NMPC #450](https://github.com/robomechanics/quad-sdk/issues/450)。 | `surveyed` |
| C07 | **Agile Navigation**；[Agile and Safe Trajectory Planning for Quadruped Navigation with Motion Anisotropy Awareness](https://arxiv.org/abs/2403.10101) | [ZWT006/agile_navigation](https://github.com/ZWT006/agile_navigation)；[作者项目页](https://zwt006.github.io/posts/AgileNav/) | **未找到根目录 LICENSE；代码复用阻塞** | `release`；[`bc63aa2ead71e224a4cc68fd7aeac3ac982f6426`](https://github.com/ZWT006/agile_navigation/commit/bc63aa2ead71e224a4cc68fd7aeac3ac982f6426) | **低/稀疏维护**；未找到正式 Release 或活跃问题单。README clone URL 存在 `github.com:` 形式错误，且依赖修改版 `legged_control`、特定 OSQP/NLopt。论文性能均为作者报告。 | `surveyed` |
| C08 | **ViPlanner**；[ViPlanner: Visual Semantic Imperative Learning for Local Navigation](https://arxiv.org/abs/2310.00982) | [leggedrobotics/viplanner](https://github.com/leggedrobotics/viplanner) | 根目录 `LICENSE` 为 BSD-3-Clause；README 的 “All right reserved” 是版权声明式措辞，复用仍应以 `LICENSE` 全文为准，并单独核验模型/资产许可 | `main`；[`6fcf3c60f6fa3b28b3a11af054d6033825923789`](https://github.com/leggedrobotics/viplanner/commit/6fcf3c60f6fa3b28b3a11af054d6033825923789) | **中等维护的研究代码**；提供 checkpoint、Docker/安装说明，无稳定语义化 Release。重要问题：[平台/相机高度迁移 #101](https://github.com/leggedrobotics/viplanner/issues/101)、[USD demo 停止 #105](https://github.com/leggedrobotics/viplanner/issues/105)、[外部数据 Open3D segfault #112](https://github.com/leggedrobotics/viplanner/issues/112)、语义资产文档缺口。 | `surveyed` |
| C09 | **Elevation Mapping CuPy + Traversability Estimation**；[Elevation Mapping for Locomotion and Navigation using GPU](https://arxiv.org/abs/2204.12876)；[MEM](https://arxiv.org/abs/2309.16818) | [leggedrobotics/elevation_mapping_cupy](https://github.com/leggedrobotics/elevation_mapping_cupy) + [leggedrobotics/traversability_estimation](https://github.com/leggedrobotics/traversability_estimation) | MIT + BSD-3-Clause 风格 | `main`：[`20a8a26b67a995b43eb44c23568854d1fed82a52`](https://github.com/leggedrobotics/elevation_mapping_cupy/commit/20a8a26b67a995b43eb44c23568854d1fed82a52)；`master`：[`14d24c059e1c43466aadf328280adf6394d78039`](https://github.com/leggedrobotics/traversability_estimation/commit/14d24c059e1c43466aadf328280adf6394d78039) | GPU 高程图仍在维护，但经典 traversability 为旧 ROS 1 代际。重要问题：[Jetson 长时 FPS 下降 #137](https://github.com/leggedrobotics/elevation_mapping_cupy/issues/137)、[ROS 2 Docker #141](https://github.com/leggedrobotics/elevation_mapping_cupy/issues/141)、[ROS 2 plane decomposition #139](https://github.com/leggedrobotics/elevation_mapping_cupy/issues/139)；经典包有 [大地图 Eigen 崩溃 #75](https://github.com/leggedrobotics/traversability_estimation/issues/75) 和 [如何接 planner #82](https://github.com/leggedrobotics/traversability_estimation/issues/82)。 | `surveyed` |
| C10 | **Wild Visual Navigation（WVN）**；[Fast Traversability Estimation for Wild Visual Navigation](https://arxiv.org/abs/2305.08510)；扩展版 [Wild Visual Navigation](https://arxiv.org/abs/2404.07110) | [leggedrobotics/wild_visual_navigation](https://github.com/leggedrobotics/wild_visual_navigation) | MIT | `main`；[`3d6d9d95d3b322956de4e9294e04639cfe30b3cd`](https://github.com/leggedrobotics/wild_visual_navigation/commit/3d6d9d95d3b322956de4e9294e04639cfe30b3cd) | **中等维护的研究代码**；提供预训练模型、rosbag、Docker/quick start。重要问题：[traversability 值饱和 #310](https://github.com/leggedrobotics/wild_visual_navigation/issues/310)、[与 elevation_mapping_cupy 融合文档 #311](https://github.com/leggedrobotics/wild_visual_navigation/issues/311)、[ROS 消息延迟依赖缺失 #308](https://github.com/leggedrobotics/wild_visual_navigation/issues/308)。 | `surveyed` |
| C11 | **LeSTA**；[Learning Self-Supervised Traversability with Navigation Experiences of Mobile Robots](https://ieeexplore.ieee.org/document/10468651) | [Ikhyeon-Cho/LeSTA](https://github.com/Ikhyeon-Cho/LeSTA) | Apache-2.0 | `master`；[`c472db219744d4643954897d8b713e52d792d272`](https://github.com/Ikhyeon-Cho/LeSTA/commit/c472db219744d4643954897d8b713e52d792d272) | **中等偏低维护**；有数据、样例 bag、模型 zoo，但 ROS 2 尚未发布。重要问题：[Docker 中 `$USER` 导致崩溃 #15](https://github.com/Ikhyeon-Cho/LeSTA/issues/15)、[ROS 2 请求 #9](https://github.com/Ikhyeon-Cho/LeSTA/issues/9)、跨数据域效果尚无明确答复。 | `surveyed` |
| C12 | **Habitat-Lab + VLN-CE**；[Habitat](https://arxiv.org/abs/1904.01201)；[VLN-CE](https://arxiv.org/abs/2004.02857) | [facebookresearch/habitat-lab](https://github.com/facebookresearch/habitat-lab) + [jacobkrantz/VLN-CE](https://github.com/jacobkrantz/VLN-CE) | MIT + MIT；场景数据另有许可 | Habitat `main`：[`0fb6f43ffe806a8088a171b036336c093bcf604e`](https://github.com/facebookresearch/habitat-lab/commit/0fb6f43ffe806a8088a171b036336c093bcf604e)；VLN-CE `master`：[`729d141b2ee10628061ada74dd3a5b9f70faeba5`](https://github.com/jacobkrantz/VLN-CE/commit/729d141b2ee10628061ada74dd3a5b9f70faeba5) | Habitat README 明确提示 v0.3.4 之后不再由 Meta 团队主动维护；VLN-CE 固定 Habitat 0.1.7/Python 3.6，属于 legacy benchmark。当前 Habitat issue 包括 [数据配置链接缺失 #2089](https://github.com/facebookresearch/habitat-lab/issues/2089)、[语义加载 #2090](https://github.com/facebookresearch/habitat-lab/issues/2090)、[PPO NaN 权重风险报告 #2226](https://github.com/facebookresearch/habitat-lab/issues/2226)。 | `surveyed` |
| C13 | **NaVILA**；[NaVILA: Legged Robot Vision-Language-Action Model for Navigation](https://arxiv.org/abs/2412.04453)，RSS 2025 | [AnjieCheng/NaVILA](https://github.com/AnjieCheng/NaVILA)；[项目页](https://navila-bot.github.io/) | Apache-2.0；模型、训练数据和 MP3D 等资产需分别核验 | `main`；[`76b98f233dd0fff05dfcd69435eec6740febff9d`](https://github.com/AnjieCheng/NaVILA/commit/76b98f233dd0fff05dfcd69435eec6740febff9d) | **活跃研究发布**；代码、8B 权重、训练/评测和 Isaac 基准已发布，但依赖 legacy Habitat。重要问题：[Habitat 0.1.7/Python 冲突 #23](https://github.com/AnjieCheng/NaVILA/issues/23)、[评测输出异常 #54](https://github.com/AnjieCheng/NaVILA/issues/54)、[Go2 部署方向错误 #57](https://github.com/AnjieCheng/NaVILA/issues/57)、[机器人部署代码请求 #29](https://github.com/AnjieCheng/NaVILA/issues/29)。 | `surveyed` |
| C14 | **BehAV**；[Behavioral Rule Guided Autonomy Using VLMs for Robot Navigation in Outdoor Scenes](https://arxiv.org/abs/2409.16484)，ICRA 2025 | [GAMMA-UMD-Outdoor-Navigation/BehAV](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV)；[项目页](https://gamma.umd.edu/researchdirections/crowdmultiagent/behav/) | Apache-2.0 | `main`；[`7ef5a48e175569a9bffa63e5725a1f378f3e55d7`](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV/commit/7ef5a48e175569a9bffa63e5725a1f378f3e55d7) | **发布不完整**；README 仅给 planner 测试命令，未找到完整编排、权重/数据和全栈 launch。重要问题：[缺 main orchestrator #1](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV/issues/1)、[cost sign/未使用参数 #2](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV/issues/2)。 | `surveyed` |
| C15 | **WildOS**；[WildOS: Open-Vocabulary Object Search in the Wild](https://arxiv.org/abs/2602.19308) | [nasa-jpl/nebula2-wildos](https://github.com/nasa-jpl/nebula2-wildos)；[项目页](https://leggedrobotics.github.io/wildos/) | Apache-2.0；基础模型/数据另核验 | `main`；[`ffab44cb5f36e5508fbe29d3dc5bcd5fe69cb572`](https://github.com/nasa-jpl/nebula2-wildos/commit/ffab44cb5f36e5508fbe29d3dc5bcd5fe69cb572) | **很新且系统负担高**；公开 checkpoint、模型下载和全管线 launch。依赖 Elevation Mapping CuPy、DLIO、Nav2。当前 issue 包括 [`unknown` map layer 来源不清 #8](https://github.com/nasa-jpl/nebula2-wildos/issues/8)。尚未找到独立、完整的第三方复现实验报告。 | `surveyed` |

### 3.2 机器人、仿真、传感器、表示与外部控制器接口

| ID | 支持机器人 / 仿真器 / ROS | 传感器假设与环境表示 | 输入 → 输出 | 规划器到运动控制器接口；外部控制器兼容性 |
|---|---|---|---|---|
| C01 Nav2 | 广泛移动机器人；官方最小 demo 为 TurtleBot；Gazebo Classic/Modern；ROS 2 | 2D occupancy/costmap 为主，可接 scan、point cloud、语义层、路线图；要求完整 TF、odom、footprint | `PoseStamped` 目标 + 地图/TF/odom → `nav_msgs/Path` → controller → `Twist`/`TwistStamped` | **高**。可只调用 planner action 获取路径，也可写 controller plugin。默认闭环仍是速度接口，需增加 path→Lite3 waypoint/trajectory bridge。 |
| C02 SLAM Toolbox | 任意提供 2D LiDAR 与里程计的 ROS 2 机器人；可与 Gazebo/Nav2 联用 | `LaserScan`、odom/TF；2D occupancy grid + pose graph | scan + odom → map、`map→odom`、序列化 pose graph | **不直接连接运动控制**。它是建图/定位层，输出交给 Nav2 或其他 planner。 |
| C03 RTAB-Map ROS | 多平台；ROS 1/ROS 2，当前默认 `ros2`；有 RGB-D、双目、3D LiDAR、Nav2 demo | RGB-D/双目/多相机/2D或3D LiDAR、IMU、odom；图优化、点云、octomap/occupancy | 多模态观测 + pose → SLAM pose、地图、点云/栅格 | **不直接连接运动控制**。通过 occupancy/costmap/pose 接 Nav2；适合替换 SLAM 层。 |
| C04 FAR | 作者仿真/地面机器人；ROS Melodic/Noetic；AEDE/外部 `vehicle_simulator` | LiDAR 点云、里程计、目标；障碍边缘多边形 + 动态 visibility graph | goal + point cloud/odom → route/path/waypoints | **较高（技术上）**。官方以 AEDE waypoint 模式执行，路径可转 Lite3 航点；但外部环境和许可证阻塞。 |
| C05 TARE | 地面与空中机器人探索；ROS Melodic/Noetic；AEDE | 点云、odom；局部高分辨率 + 全局稀疏双层探索表示 | 未知空间观测 → exploration viewpoints/path | **中等**。输出探索路径可交 waypoint executor，但任务是覆盖探索，不是给定目标导航。 |
| C06 Quad-SDK | Spirit、Go1/Go2/Go2-W、A1/A2/B2、Spot、Vision60 等；Gazebo Harmonic、MuJoCo、Isaac Sim beta；ROS 2 Jazzy | 机器人全状态、地形/高程、接触；body state/terrain grid | goal/reference → RRT body path → NMPC body plan → footstep/GRF → leg command | **中等**。提供自定义 `LegController`/learned controller hook，但纵向耦合强；Lite3 需新增模型、driver、估计和控制适配。 |
| C07 Agile | Unitree A1；Gazebo；ROS Noetic | FAST-LIO2/全局点云、概率 occupancy、机器人状态；考虑方向各向异性 | goal/map → kinodynamic path → nonlinear optimized trajectory → NMPC/WBC | **低到中等**。最自然接口是时间参数身体轨迹；上游与修改版 `legged_control` 紧密绑定，替换为 Lite3 waypoint 控制会损失方法核心。 |
| C08 ViPlanner | ANYmal C/D 已测试；作者称可配置其他机器人；Isaac Sim/IsaacLab；ROS Noetic | 深度 + 语义图像，机器人状态/目标；语义可通行 cost | RGB/semantic/depth + goal → `/viplanner/path` (`nav_msgs/Path`) | **高**。源码中的 `pathFollower` 是独立节点，将 Path 转为默认 `/cmd_vel` `TwistStamped`；可直接替换 follower。 |
| C09 Elevation/Traversability | ANYmal/TurtleBot 示例等；ROS 1 主线、ROS 2 分支；仿真/rosbag | point cloud/depth/image + pose；GPU 2.5D elevation/grid map、多模态层、几何 traversability | sensor + state → elevation、variance、semantic/traversability/risk layers | **间接高**。输出 cost/grid layer，交给 Nav2/ViPlanner/自定义 planner；不是执行器。机器人 footprint 和足端能力必须重新参数化。 |
| C10 WVN | ANYmal 实验，Jackal/通用地面机器人配置；ROS 1；Docker/rosbag | RGB、位姿/本体经验；预训练视觉特征 + 在线自监督 | image + navigation experience → pixel/instant/global traversability | **间接高**。把视觉可通行性融合到高程/代价图，再由 planner 输出路径；不应直接驱动 Lite3。 |
| C11 LeSTA | 通用移动机器人；ROS Noetic；样例 rosbag；ROS 2 未发布 | 3D LiDAR/高度图 + 手动行驶经验；机器人特定风险/可通行图 | 经验数据 → 标签 → 模型 → traversability point/grid map | **间接高**。输出风险层，需独立 planner；适合 Lite3 收集自身通过经验后再训练，不是第一阶段。 |
| C12 Habitat/VLN-CE | Habitat-Sim 中的虚拟 agent；非真实 ROS 栈 | RGB-D、GPS/compass/pose、语言指令；MP3D 等场景与连续/离散环境 | language + observations → simulator actions/continuous navigation policy | **低（直接真机）/高（算法评测）**。需要把 simulator action 转为 metric subgoal，再接真实 planner；不能直接接 Lite3。 |
| C13 NaVILA | 作者实机包括 Unitree Go2/人形；IsaacLab 与 legacy Habitat/VLN-CE | 单目 RGB/视频 + 语言；低层策略另用视觉/高度信息 | language + video → 语言中间动作（如“前进 75 cm”）→ visual locomotion RL | **中等**。应只复用高层，把语言动作解析为受限 metric subgoal，再由 Nav2/ViPlanner 和 Lite3 控制器执行；不要直接复用硬编码机器人动作映射。 |
| C14 BehAV | 作者报告四足实机；ROS 2 Galactic；未找到完整 simulator | RGB + VLM/LLM + LiDAR occupancy；behavioral cost map | language → landmark/行为规则；RGB/LiDAR → cost map；MPC → 局部动作 | **潜在中等**，但当前仓库缺完整 orchestrator，planner 脚本的接口和时序需源码重构前先独立核验。 |
| C15 WildOS | README 示例 namespace 为 `spot1`；其他机器人清单未明确；ROS 2 Jazzy | RGB、DLIO、Elevation Mapping、稀疏 graph、开放词汇查询 | query + visual/geometric graph → frontier/object scores → graph goal/path → Nav2 | **较高（分层）**。其几何执行依赖 Nav2，可在 Nav2 path/cmd 边界替换为 Lite3 waypoint bridge；但系统依赖链重。 |

### 3.3 环境、资产、最小入口、复现难度与 Lite3 适配

| ID | OS / CUDA / Python / 硬件 | 权重、数据、Docker/conda | 官方最小运行或演示入口（仅记录，未运行） | 第三方复现证据 | 难度、Lite3 修改点与最大风险 |
|---|---|---|---|---|---|
| C01 | 建议 Ubuntu 24.04 + ROS 2 Jazzy；无 CUDA 强制要求；Gazebo/RViz 需 OpenGL | 无 ML 权重；二进制、源码、Docker/devcontainer 均有 | `sudo apt install ros-$ROS_DISTRO-navigation2 ros-$ROS_DISTRO-nav2-bringup ros-$ROS_DISTRO-nav2-minimal-tb*`；`ros2 launch nav2_bringup tb3_simulation_launch.py headless:=False` | 大量公开使用与 issue，但本轮未核验某个独立复现包；不能算本项目 reproduced | **低到中**。修改 TF、URDF footprint、传感器、costmap、速度/加速度；增加 path→waypoint bridge。风险是把平面 costmap 当作足式可通行性，以及 ROS 发行版与 Lite3 Foxy 不一致。 |
| C02 | ROS 2 对应 Ubuntu；CPU 即可 | ROS 二进制；无权重；有 launch/config | 常见入口为 `online_async_launch.py`/`online_sync_launch.py`；确切机器人 launch 需按传感器选择 | 有用户 issue 和 Nav2 生态使用；未核验独立可重复脚本 | **中**。需 2D LiDAR、稳定 odom、正确 scan frame；风险为腿式里程计漂移、振动和地图保存/加载边界。 |
| C03 | Humble 起的 ROS 2；CPU 可运行，GPU 可选；Docker 多发行版 | 无必需 ML 权重；Docker、binary、丰富 demo | `sudo apt install ros-$ROS_DISTRO-rtabmap-ros`；再选择官方 RGB-D/双目/LiDAR demo | 有大量社区使用和 issue；本轮未核验特定 Lite3/四足复现 | **中到高**。传感器组合和同步参数多；需将输出稳定转换到 Nav2 map/costmap。风险是实时性能、回环跳变和多模态参数复杂度。 |
| C04 | Ubuntu 18.04/20.04；ROS Melodic/Noetic；CPU | 无权重；依赖外部 AEDE；未找到官方 Docker/conda | `catkin_make`；AEDE：`roslaunch vehicle_simulator system_indoor.launch`；FAR：`roslaunch far_planner far_planner.launch` | issue 显示多人尝试，但存在缺 simulator、停滞和真机问题；无独立成功协议被核验 | **中（技术）/高（整体）**。需 ROS1→ROS2 bridge 或隔离，适配点云/odom/waypoint；**最大风险为无许可证和外部运行环境不闭合**。 |
| C05 | Ubuntu 18.04/20.04；ROS Melodic/Noetic；OR-Tools 对架构/GLIBC 敏感 | 无权重；外部 AEDE；未找到 Docker/conda | 构建 TARE 与 AEDE 后运行相应 launch；README 的路径以 `melodic-noetic` 为准 | issue 有编译/真机尝试，但不构成成功复现 | **高**。探索任务、外部 simulator、OR-Tools 二进制、ROS1、无许可证；对最小 point-goal 闭环价值低。 |
| C06 | Ubuntu 24.04、ROS 2 Jazzy；约 10 GB 工作区；HSL/IPOPT；x86 Docker 含 CUDA 12.8；JetPack 6.x 支持部署 | Docker x86/arm-mpc/arm-learned；无统一通用 checkpoint；learned controller 支持 ONNX | `./setup.sh` → `colcon build` → `ros2 launch quad_utils quad_gazebo.py` → stand topic → `ros2 launch quad_utils quad_plan.py` | 官方文档与用户 issue；已有失败报告，但本轮未核验成功第三方流水线 | **高**。需 Lite3 URDF/dynamics/driver/state estimator/leg controller；HSL 注册与版本、实时控制、纵向耦合是主要风险。 |
| C07 | Ubuntu 20.04、ROS Noetic；C++，OpenCV/Eigen/OSQP 0.6.3/NLopt 2.7.1；论文实机为 Xavier NX + NUC | 无公开通用权重；依赖修改版 `legged_control` | README 的 A1 Gazebo/规划/控制 launch；clone 行需手工修正 URL | 未找到系统性第三方复现证据 | **高**。若只取 trajectory planner，需要定义 Lite3 的动态可行域和轨迹跟踪器；无许可证、依赖钉死和控制绑定是最大风险。 |
| C08 | Ubuntu 20.04、ROS Noetic；CUDA 11.7、PyTorch 2.0.x/mmcv 2.0.0 时代环境；Isaac Sim/IsaacLab；Jetson 有额外说明 | Google Drive checkpoint/config；pip editable install；Docker | `pip install -e .[standard]` 或 inference extra；ROS：`roslaunch viplanner_node viplanner.launch` | 多个外部 issue 说明有人尝试数据/部署；未核验独立成功复现报告 | **高但可控**。先做 checkpoint 图像推理，再 ROS path；需相机内外参、机器人尺寸/高度、语义编码和 ROS1/2桥。最大风险为旧 CUDA/mmcv/Isaac 资产组合。 |
| C09 | 主线 ROS 1/CUDA/CuPy；ROS 2 分支；NVIDIA GPU；经典 traversability CPU/ROS1 | Docker；TurtleBot 示例；无必需学习权重 | `cd docker && ./run.sh`；示例 `roslaunch elevation_mapping_cupy turtlesim_simple_example.launch` | issue 中有 Jetson、ROS2、不同平台尝试；存在长时 FPS 和容器失败 | **中到高**。需 Lite3 足迹、传感器噪声、map frame、坡度/台阶阈值；最大风险为 ROS 代际、GPU时延和 2.5D 表示盲区。 |
| C10 | ROS 1；CUDA-enabled GPU，README 以 CUDA 12.0 为目标；纯 Python 路径 | 预训练模型、示例图像、rosbag、Docker | `python3 quick_start.py`；全节点 `roslaunch wild_visual_navigation_ros wild_visual_navigation.launch` | issue/rosbag 使用记录；无本轮核验的独立 end-to-end 成功报告 | **高**。需 RGB 标定、位姿与机器人经验信号，再把输出接 costmap。风险为在线学习稳定性、监督饱和、消息时序和场景迁移。 |
| C11 | Ubuntu 20.04、ROS Noetic；PyTorch 2.2.2/LibTorch 2.6；官方建议 CPU-only 便于安装 | 公开数据、样例 rosbags、两个预训练模型；Docker 标为 TODO/存在 issue | `roslaunch lesta label_generation.launch`；训练；`roslaunch lesta traversability_prediction.launch` | issue 显示容器与跨数据使用尝试；未核验独立完整复现 | **中到高**。先用模型 zoo smoke，再采 Lite3 数据；风险为动态物体伪影、高度图噪声、ROS1 和机器人特定域偏移。 |
| C12 | Habitat-Lab Python ≥3.9；VLN-CE 固定 Python 3.6、Habitat 0.1.7；GPU渲染通常有利 | MP3D/HM3D/R2R/RxR 等数据；模型权重；场景下载常需单独许可；旧 Docker | Habitat 单元测试/示例；VLN-CE 按 README 执行 `run.py --exp-config ... --run-type eval/inference` | 学术基准广泛使用；但版本老，当前环境复现仍需实际验证 | **高**。只作为离线 benchmark；需要 action→metric subgoal 适配。风险为数据许可、旧 Python/渲染栈和模拟动作与真机差距。 |
| C13 | Conda/Python 3.10 主环境；legacy Habitat 0.1.7、FlashAttention2、CUDA/PyTorch 特定 wheel；8B 模型需要高显存，官方统一下限未找到 | Hugging Face 8B checkpoints；VILA/VLN-CE/R2R/RxR/MP3D；YouTube 原视频因版权未发布；Isaac Sim benchmark | `./environment_setup.sh navila`；评测 `bash scripts/eval/r2r.sh CKPT_PATH 1 0 "0"` | issue 包含 RTX 4090 评测和 Go2 部署尝试，但有输出/方向错误；不能视为独立成功 | **很高**。先只复现评测和中间动作；需动作 schema、可达性验证、VLA latency、模型/数据许可。最大风险为 legacy Habitat 与实机动作映射。 |
| C14 | ROS 2 Galactic + PyTorch；硬件/CUDA/模型版本未完整钉死 | 未找到完整权重、数据、Docker、conda 或全栈 launch | `cd planning/ && python3 behav-planner.py` | issue 明确指出缺 orchestrator 和 cost 逻辑疑问 | **很高**。更适合阅读 cost-map/VLM 设计，不宜作为首个复现。风险是发布不完整和控制逻辑含义不清。 |
| C15 | Ubuntu/ROS 2 Jazzy、Python ≥3.10、CUDA GPU；作者说明 RTX 4090 训练、Jetson AGX Orin 部署 | 部分 checkpoint 内置/可下载；数据与项目页；依赖多个外部 ROS 2 栈 | 模型 smoke：`python explorfm/explorfm_model.py`；全栈 `ros2 launch visual_navigation wildos_launch.py ...` + graph mapper/planner launch | 项目很新；未找到独立全管线复现；现有 issue 聚焦 map layer 语义 | **很高**。需先分别复现 DLIO、高程图、Nav2、ExploRFM、graph mapper。风险是依赖链、GPU/嵌入式负担和接口文档尚在形成。 |

### 3.4 未纳入 15 个可复现候选的已核验线索

| 项目 | 核验结论 | 处理方式 |
|---|---|---|
| **Skill-Nav** | [论文](https://arxiv.org/abs/2506.21853)和[正式开放获取文章](https://doi.org/10.1007/s44336-025-00015-y)已核验。论文采用 base frame 下 2D 相对航点，A* 路径按约 0.5–3 m 间距采样；论文也讨论航点落在缝隙/边缘等坏例。**Code availability 写的是“可向第一作者获取”，未找到公开 canonical 仓库和开源许可证。** | 作为“waypoint-interface locomotion”架构与风险参考；不作为本轮开源复现对象。 |
| **VP-Nav** | [Coupling Vision and Proprioception for Navigation of Legged Robots](https://arxiv.org/abs/2112.02094)提供“视觉/本体感觉 cost map → fast marching → velocity command → locomotion policy”重要分层参考；公开代码完整性与当前维护不及前述候选。 | 作为接口和安全 advisor 文献基线，不列入首轮仓库。 |
| **QTOS / CHAMP** | QTOS 更偏全栈四足优化与特定硬件；CHAMP 是经典开源四足运动控制框架，导航研究价值主要在底层接口而非现代自主导航。 | 可用于控制层对照，不作为 `machine-dog-nav` 第一导航基座。 |
| **SCAN-Planner、SEA-Nav 等 2026 新工作** | 论文方向与四足 3D 局部碰撞/语义导航相关，但截至核验日公开代码、稳定文档或长期维护证据不足，或本轮未找到可确认的 canonical 实现。 | 进入后续雷达列表，不据此改变第一轮复现排序。 |

---
## 4. 导航层—运动控制层接口专项比较

### 4.1 接口并不是“消息格式”问题，而是责任边界问题

导航与运动控制之间的接口至少同时规定：

1. **空间语义**：目标在 `map`、`odom`、`base_link` 还是相机坐标系中；二维还是三维；姿态是否必需。
2. **时间语义**：一次性目标、滚动目标、带时间戳轨迹，还是持续高频 setpoint；旧指令何时失效。
3. **动态语义**：谁负责限速、加速度、转向曲率、步态切换、身体姿态和落足约束。
4. **安全语义**：谁负责碰撞检查、未知空间处理、失联、急停、侧翻/打滑检测和不可达目标拒绝。
5. **反馈语义**：控制器返回当前位置、跟踪误差、目标完成、失败原因，还是只暴露里程计。

因此，“几何航点”只有在上述契约被固定后才是一个可复现接口。单纯发布 `(x,y)` 并不能形成可验证的闭环。

### 4.2 六类主要接口的工程比较

| 接口 | 常见消息/表示 | 坐标系与频率 | 碰撞安全与地形能力 | 训练成本与可解释性 | 真机主要风险 | Lite3 阶段适配结论 |
|---|---|---|---|---|---|---|
| **速度指令** | `geometry_msgs/Twist` / `TwistStamped`；`vx, vy, wz` | 通常在 `base_link`；10–100 Hz，底层策略可能更高频；要求 watchdog | 局部规划器必须在每周期负责避障；速度本身不表达未来几何、落足或地形风险 | 无训练要求；最易记录与调试；但很难解释“为什么选择这条路径” | 延迟、抖动、过期命令、控制器与 planner 动力学不匹配；短时障碍制动距离不足 | **最兼容的回退接口**。Lite3 厂商公开 ROS 2 bridge 使用 `/cmd_vel`；若 `machine-dog` 只收速度，应先采用这一边界，而不是伪造 waypoint 支持。 |
| **几何航点/目标位姿** | `PoseStamped`、相对 `(x,y[,yaw])`、短 waypoint queue | 可在 `map/odom` 给绝对目标，或在 `base_link` 给相对目标；典型 0.5–10 Hz/到点更新 | 可由高层 planner 做几何碰撞检查；低层仍必须处理航点间动态障碍、局部地形和不可实现转向 | 不要求训练；可视化、回放、单元测试和跨机器人迁移较容易 | 航点位于障碍边缘/台阶/空洞；稀疏航点造成“切角”；坐标漂移；到点振荡；低层可能直线追踪穿越障碍 | **推荐的第一阶段项目边界，但必须条件化**。只有在 `machine-dog` 已定义可靠 waypoint/pose follower 时才直接使用；否则由独立 bridge 将 path/waypoint 转安全速度。 |
| **短期路径/轨迹** | `nav_msgs/Path`；带速度/时间的 SE(2)/SE(3) trajectory；多项式/B-spline | 路径一般无严格时间；轨迹含时间参数，20–200 Hz 重规划/跟踪 | 可显式表达曲率、速度、动态可行性；可在 horizon 内碰撞检查；仍未必表达足端接触 | 轨迹规划无需学习，学习型 planner 可增加训练成本；可解释性高于端到端策略 | 控制器必须与轨迹动力学和时钟严格一致；时间戳、延迟和重规划切换容易造成跳变 | **路线 B/C 的自然升级**。Nav2 与 ViPlanner 均可在 `nav_msgs/Path` 边界拆分；若 Lite3 能跟踪短轨迹，其性能上限高于单航点。 |
| **像素目标/图像空间目标** | `(u,v)`、分割 mask、热力图、image-goal embedding | 相机坐标/图像平面；随图像 5–30 Hz；必须依赖标定、深度或视觉伺服 | 近场语义/目标指向有优势；单目像素不直接给可达距离、遮挡与地面几何 | 通常需要视觉模型、数据或预训练模型；中等可解释性，可叠加可视化 | 深度尺度、相机遮挡、照明、域偏移、标定误差；像素目标可能落在不可通行物体上 | **不宜作为第一底层接口**。应先变成 3D/地面 metric subgoal 或 cost layer，再交几何 planner。 |
| **语言中间动作** | `“forward 0.75 m”`、`turn left`、skill token、JSON action schema | 语言/任务语义坐标；通常 0.1–2 Hz；强异步 | 高层可表达长程意图和规则，但本身不保证几何可达、实时避障或动力学安全 | 大模型/数据/推理成本高；人类可读，但解析与模型行为未必可重复 | 幻觉、左右/距离错误、延迟、不可达动作、提示词敏感、模型更新导致行为漂移 | **只适合路线 C 高层**。必须经结构化解析、能力/安全校验和 planner 投影；不得直接驱动电机或把自由文本映射成无检查的 Lite3 动作。 |
| **足步/落足点** | 每条腿的 contact schedule、foothold position、swing trajectory、GRF | 世界/机体/地形 frame；通常 50–500 Hz，强实时 | 能直接表达缝隙、台阶、接触和全身稳定；是粗糙地形能力最强的接口之一 | 需要准确模型、高程图和优化/学习控制；可解释但参数复杂 | 模型误差、状态估计漂移、时序抖动、接触估计错误可直接导致跌倒 | **不适合作为第一导航接口**，除非 `machine-dog` 本身就公开并稳定支持足步目标。可作为长期 locomotion-aware planning 研究方向。 |

### 4.3 其他值得保留的中间表示

| 表示 | 典型用途 | 与 Lite3 的关系 |
|---|---|---|
| **可通行性/风险代价场** | Elevation Mapping、WVN、LeSTA 等输出 `grid_map`、像素风险或多模态代价；供全局/局部 planner 使用 | 非控制命令，但最适合把“Lite3 能否通过”注入 Nav2/ViPlanner。应保留原始概率、置信度和时间戳，而不是过早二值化。 |
| **走廊/安全凸集** | 轨迹优化在无碰撞 corridor 中生成平滑路径 | 比离散航点更能约束航点之间的安全区域；适合路线 B 的轨迹 planner。 |
| **行为/技能 primitive** | `walk_forward`、`turn_in_place`、`climb_step`、`recover` 等有限状态动作 | 比自由文本可靠，但仍需能力 manifest、前置条件、终止条件和失败回退。 |
| **身体状态/姿态参考** | base pose、height、roll/pitch、yaw、body velocity | 可连接地形感知与全身控制；若 `machine-dog` 只支持速度，不应擅自加入未验证的身体姿态命令。 |

### 4.4 为什么几何航点适合作为第一阶段接口

几何航点对当前项目的价值主要不是“性能最优”，而是**建立稳定、可替换、可测量的仓库边界**：

- `machine-dog-nav` 可以把不同上游统一为 `Path/waypoint`：Nav2 的规划 action、ViPlanner 的 `/viplanner/path`、FAR 的 route、VLA 的 metric subgoal 都可投影到同一几何层。
- `machine-dog` 可以独立评测“给定局部目标能否到达”，导航仓库则独立评测“目标是否合法、路径是否无碰撞、何时重规划”。
- 失败更易归因：规划失败、坐标变换失败、航点选择错误、跟踪失败、状态估计漂移可以分别记录。
- 与具体运动策略解耦。RL locomotion checkpoint 可更换，只要维持 waypoint contract；导航算法也可更换，无需重新训练低层。
- 适合回放和验收：固定地图、固定起点、固定 waypoint 序列，可重复计算到达率、路径偏差、停滞和超时。

但其限制不能被隐藏：

1. **航点间的连线不天然安全。** planner 认为 path 安全，不代表低层 follower 会严格沿 path；只追下一个点可能切角。
2. **航点不含动态可行性。** 它通常不表达速度、加速度、转向半径、步态、身体姿态或落足约束。
3. **二维航点可能掩盖足式地形风险。** 对台阶、悬空、负障碍和狭缝，SE(2) 可达不等于足式可通过。
4. **相对航点依赖短时状态估计，绝对航点依赖全局定位。** 两者的漂移模式不同，必须显式选择。
5. **VLA 生成的“距离动作”并不自动成为可靠航点。** 必须用当前 pose 变换、裁剪、投影到 free/traversable region，并在执行前重新验证。

### 4.5 推荐的第一阶段接口契约

建议 `machine-dog-nav` 内部先定义一个与具体 ROS 消息解耦的规范，再映射到 ROS 2：

```text
WaypointCommand
  command_id: uint64
  stamp: monotonic/ROS time
  frame_id: map | odom | base_link          # 必选且只允许白名单
  target_position: x, y [, z]
  target_yaw: optional
  position_tolerance: m
  yaw_tolerance: rad
  max_speed: optional, bounded by controller capability
  expiry: duration
  stop_at_goal: bool
  source_path_id / source_planner
  safety_context: map_version, costmap_stamp, traversability_confidence
```

对应反馈至少应包含：`accepted / active / reached / rejected / timeout / preempted / safety_stop / controller_fault`，当前 pose、目标误差、最后一次有效状态时间和失败原因。执行器必须支持新 command 抢占旧 command、过期清零、失联进入安全状态，并拒绝未知 frame 或超出能力包络的目标。

第一阶段仍应保留两个桥接实现的设计位置：

- **Path → Waypoint bridge**：从 `nav_msgs/Path` 按弧长、曲率、障碍裕度和可见性选取局部目标；不能只按固定点数下采样。
- **Waypoint → Twist bridge**：当低层只接受速度时，用受限 path follower 产生 `TwistStamped`，并独立实现碰撞监控、限速、watchdog 和停止逻辑。

这使“几何航点”成为研究接口，而不要求机器人厂商或现有 RL 控制器天然提供同名 API。

---
## 5. Top 5 深度对比、100 分制评分与淘汰理由

### 5.1 评分解释

分数衡量**对本项目当前阶段的适配性**，不是论文影响力或算法先进性。各项满分严格按用户给定权重：外部控制器兼容 25、上游可复现性 20、依赖/仿真/算力 15、许可证 10、维护 10、博士研究价值 15、仿真到真机 5。信息不足时既扣分也降低置信度。

| 排名 | 候选 | 外部 Lite3 控制器兼容 25 | 上游复现/文档 20 | 依赖/仿真/算力 15 | 许可证 10 | 维护 10 | 博士价值 15 | Sim→Real 5 | 总分 | 置信度 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | **Nav2** | 23 | 20 | 13 | 8 | 10 | 12 | 4 | **90** | 高 |
| 2 | **ViPlanner** | 23 | 15 | 8 | 10 | 7 | 15 | 4 | **82** | 中高 |
| 3 | **Quad-SDK** | 15 | 15 | 6 | 10 | 8 | 15 | 5 | **74** | 中 |
| 4 | **FAR Planner** | 21 | 11 | 11 | 0 | 4 | 13 | 4 | **64** | 中低 |
| 5 | **Agile Navigation** | 12 | 9 | 7 | 0 | 3 | 15 | 4 | **50** | 低到中 |

### 5.2 第一名：Nav2 — 90/100

| 评分项 | 分数 | 证据与理由 |
|---|---:|---|
| 外部控制器兼容 | 23/25 | `ComputePathToPose/ThroughPoses` 可独立输出 `nav_msgs/Path`；Controller Server 与 planner 通过 path 分层；支持自定义 controller plugin。扣 2 分是因为默认输出仍是速度控制，且足式 waypoint bridge 与 traversability layer 需项目实现。 |
| 上游复现/文档 | 20/20 | 官方二进制、稳定发行版、完整文档、TurtleBot 仿真 smoke、教程、插件 API、CI、Docker/devcontainer 均可审计。第一轮无需源码构建。 |
| 依赖/仿真/算力 | 13/15 | CPU 即可，无 CUDA/权重；标准 ROS 2 + Gazebo/RViz。扣分来自 ROS 发行版一致性、图形/仿真体积及完整 TF/costmap 配置。 |
| 许可证 | 8/10 | 大部分宽松，但仓库按包混合 Apache/BSD/LGPL；必须生成 package-level SBOM/NOTICE，不能把整个仓库简单写成单一 Apache。 |
| 维护 | 10/10 | 2026-07-22 仍有提交，多个 ROS 发行版 CI/二进制，专业维护与活跃 issue/PR。 |
| 博士价值 | 12/15 | 是强可重复系统基线和混合系统骨架，可系统比较 A*/Hybrid A*/lattice/MPPI/RPP/学习插件；其本身不是四足地形研究新贡献，故非满分。 |
| Sim→Real | 4/5 | ROS 2 标准接口、传感器/控制插件广泛用于真机。扣 1 分是平面移动机器人假设与四足地形/侧向运动差距。 |

**结论：**最适合作为第一复现对象和长期几何基座。第一阶段应先复现官方 stock demo，再只读调用 planner action；不要一开始就修改 Nav2 或把 Lite3 接入其完整控制链。

### 5.3 第二名：ViPlanner — 82/100

| 评分项 | 分数 | 证据与理由 |
|---|---:|---|
| 外部控制器兼容 | 23/25 | 源码明确发布 `/viplanner/path` (`nav_msgs/Path`)，独立 `pathFollower` 才转 `/cmd_vel`。可绕开 ANYmal follower，直接接 Lite3 waypoint/trajectory bridge。扣分来自相机/机器人参数与路径语义仍需确认。 |
| 上游复现/文档 | 15/20 | 有论文、项目页、checkpoint/config、pip、ROS node、Isaac demo 与训练文档。扣分来自研究代码环境、语义资产和当前 issue 中的 demo/数据失败案例。 |
| 依赖/仿真/算力 | 8/15 | 公开模型可免训练，但环境锁在 Ubuntu 20.04/ROS Noetic、CUDA 11.7、PyTorch 2.0/mmcv/Isaac 组合，且需要 RGB-D/语义推理。 |
| 许可证 | 10/10 | 根目录 `LICENSE` 明确给出 BSD-3-Clause 授权。README 同时使用 “All right reserved” 的版权声明式措辞；应保留版权与许可文本，并将 checkpoint、Matterport/CARLA/Isaac 资产许可单独建账。 |
| 维护 | 7/10 | 2026 年仍有提交/issue，但属于单实验室研究代码，未找到稳定 release 维护承诺。 |
| 博士价值 | 15/15 | 直接覆盖视觉局部规划、语义代价、sim-to-real、外部低层控制器接口，并可与 Nav2/地形栈比较。 |
| Sim→Real | 4/5 | 官方有 ANYmal C/D ROS 真机路径和 D435i 配置。扣分来自相机高度、机器人尺寸与场景域迁移，README 明确提示显著不同平台可能需要重训。 |

**结论：**最有价值的第二阶段学习型局部 planner。第一步只做 checkpoint/demo 和 path 输出验证，不把 Isaac locomotion 成功等同于 Lite3 可用。

### 5.4 第三名：Quad-SDK — 74/100

| 评分项 | 分数 | 证据与理由 |
|---|---:|---|
| 外部控制器兼容 | 15/25 | 架构模块化并提供自定义 `LegController`/learned-controller hook，但全栈从 body path、NMPC、footstep 到腿控制纵向耦合。替换底层会改变方法闭环，适配工作远高于 path follower。 |
| 上游复现/文档 | 15/20 | 当前官方 ROS 2 Jazzy 文档、setup、Gazebo/MuJoCo/Isaac、控制器扩展说明较完整。扣分来自 HSL 注册依赖、版本敏感以及用户报告的 planner/NMPC 失败。 |
| 依赖/仿真/算力 | 6/15 | ROS 2 Jazzy 方向与项目长期方向一致，但约 10 GB workspace、HSL/IPOPT、多个 simulator、动力学和实时控制显著增加负担。 |
| 许可证 | 10/10 | MIT 明确。HSL 等第三方依赖有独立获取/授权条件，需单列。 |
| 维护 | 8/10 | 2026 有文档/代码更新与 ROS 2 迁移；仍有高影响 open issue，且研究框架的支持能力有限。 |
| 博士价值 | 15/15 | 可研究 locomotion-aware/global body planning、NMPC、footstep 和 learned controller，是长期高价值对照。 |
| Sim→Real | 5/5 | 目标就是多四足仿真/硬件纵向集成，支持多机器人和 ARM 部署路径；这不等于 Lite3 即插即用。 |

**结论：**第三候选，但应作为**独立纵向研究支线**复现。只有在 Lite3 低层开放足够的状态/动力学/腿命令接口后，才考虑组件级移植。

### 5.5 第四名：FAR Planner — 64/100

| 评分项 | 分数 | 证据与理由 |
|---|---:|---|
| 外部控制器兼容 | 21/25 | 输出 route/waypoint，官方 AEDE 以 waypoint mode 执行，技术上容易换执行器。扣分来自接口文档依赖外部环境，消息与 frame 契约需源码确认。 |
| 上游复现/文档 | 11/20 | README 有完整 ROS1 仿真步骤和多个环境；但 `vehicle_simulator` 在外部 AEDE，issue 中出现缺包、停滞和真机询问。 |
| 依赖/仿真/算力 | 11/15 | CPU、ROS1，算法本身轻；扣分来自 Ubuntu 18.04/20.04、AEDE 大环境和 ROS1↔ROS2 桥。 |
| 许可证 | 0/10 | 根目录未找到 LICENSE。公开可读不等于获得复制、修改、再发布许可；在作者补充许可前不得把源码合入项目。 |
| 维护 | 4/10 | commit 和 issue 较稀疏，无正式 release；关键部署问题未形成维护闭环。 |
| 博士价值 | 13/15 | 动态 visibility graph、未知空间 attemptable route、DARPA SubT 背景有高研究价值。 |
| Sim→Real | 4/5 | 设计和演示面向复杂真实环境；但本项目尚无独立复现，且真机 issue/传感器边界仍未闭环。 |

**结论：**可作为“许可证隔离的只读基准”或联系作者后复现；在许可解决前不得进入 `machine-dog-nav` 主代码。

### 5.6 第五名：Agile Navigation — 50/100

| 评分项 | 分数 | 证据与理由 |
|---|---:|---|
| 外部控制器兼容 | 12/25 | 输出并跟踪动态可行轨迹，理论上可替换 tracker；但方法核心与修改版 `legged_control`、NMPC/WBC 和 A1 模型绑定。降格为 waypoint 会丢失运动各向异性/动态可行性贡献。 |
| 上游复现/文档 | 9/20 | README 给出依赖和 launch；但 clone URL 有错误、无 Docker/lockfile/release、依赖版本需要手工源码安装。 |
| 依赖/仿真/算力 | 7/15 | CPU planner 可行，但 ROS Noetic、OSQP 0.6.3、OSQP-Eigen、NLopt 2.7.1、修改控制器和 Gazebo 栈负担高。 |
| 许可证 | 0/10 | 根目录未找到 LICENSE，代码复用阻塞。引用的子模块还需逐项核验许可。 |
| 维护 | 3/10 | 默认 `release` 分支有代码，但近期维护、release 与 issue 支持证据有限。 |
| 博士价值 | 15/15 | 四足轨迹规划、运动各向异性和规划—控制耦合与博士研究高度相关。 |
| Sim→Real | 4/5 | 论文报告 A1 真机与计算平台；对 Lite3 的模型、控制接口和传感器迁移仍大。 |

**结论：**适合后续论文复现或算法重实现对照，不适合作为第一闭环基座；许可和控制绑定是双重阻塞。

### 5.7 其他候选未进入 Top 5 的原因

- **SLAM Toolbox、RTAB-Map、Elevation Mapping/WVN/LeSTA**：是高价值的建图/感知/代价模块，但不是完整 point-goal 导航系统；应按层集成，不能与完整 Nav2 直接按同一目标评分。
- **TARE**：面向自主探索而非第一阶段给定目标闭环；同时存在 ROS1、外部 simulator、OR-Tools 和许可证阻塞。
- **Habitat/VLN-CE、NaVILA**：适合高层语义/VLN 研究，但 legacy Habitat、数据/模型和 GPU 负担过高；不能先于几何闭环。
- **BehAV**：仓库只给 planner 脚本，issue 指出缺 main orchestrator 且 cost 逻辑有疑问；公开程度不足以作为第一基座。
- **WildOS**：2026 新系统、ROS 2 Jazzy、分层理念强，但要求 DLIO、Elevation Mapping、Nav2 和大型视觉 backbone；应在各依赖独立 reproduced 后再做系统级复现。
- **Skill-Nav**：论文架构相关，但截至核验日无公开 canonical 仓库和开源许可证，因此不属于“真正可检查源码并直接复现”的候选。

---
## 6. 推荐的分阶段路线

### 6.1 统一的状态门控

所有路线均遵守同一状态机，不能跳级：

```text
surveyed
  └─ 上游原始命令在固定环境实际成功，并保存日志/版本/视频/轨迹
       → reproduced
          └─ 上游输出通过已定义接口接入 machine-dog / Lite3 仿真控制
               → integrated
                  └─ 预先声明的场景、指标、异常注入和安全测试通过
                       → validated
```

本报告完成后，所有候选仍仅为 `surveyed`。

### 6.2 路线 A：最快建立“几何路径/航点 → Lite3 运动控制”最小闭环

| 项目 | 内容 |
|---|---|
| **目标** | 先证明标准几何导航的上游可以稳定产生路径，再证明 `machine-dog` 能按统一 waypoint contract 接受目标并回传状态。第一轮不加入学习感知、粗糙地形或 VLA。 |
| **上游基座** | **Nav2**。先运行官方 TurtleBot 仿真；随后只使用 Planner Server 的 `ComputePathToPose/ThroughPoses` 输出，避免一开始把 Nav2 Controller Server 与 Lite3 控制器耦合。 |
| **最小复现任务 A0** | 在干净的 Ubuntu 24.04 + ROS 2 Jazzy 环境安装官方二进制并运行 `tb3_simulation_launch.py`。固定地图、起点、目标和 Nav2 参数，保存完整运行证据。 |
| **最小复现任务 A1** | 调用 planner action 获取 `nav_msgs/Path`；验证 path frame、时间戳、首尾点、碰撞代价、空路径和不可达目标行为。此步骤仍不接 Lite3。 |
| **最小集成任务 A2（接口确认后）** | `Path → local waypoint` 选择器输出项目定义的 `WaypointCommand`。若 `machine-dog` 只支持速度，则使用 `Path/waypoint → TwistStamped` 安全 follower；不要把速度接口包装成“原生 waypoint 控制”。 |
| **所需环境** | 推荐隔离的 Jazzy 工作站/容器；CPU 仿真即可。若 Lite3 侧仍是 ROS 2 Foxy 或非 ROS 进程，先通过独立网络/API bridge 交换版本化消息，不把两个 ROS 发行版混装到同一进程。 |
| **预期产物** | `environment_manifest.txt`、apt/仓库锁定文件、launch 日志、ROS bag、RViz/Gazebo 视频、目标与 action result、`nav_msgs/Path`、`cmd_vel`、TF 诊断、碰撞/到达指标；后续再加 waypoint command/feedback 记录。 |
| **通过条件：A0 上游 reproduced** | ① 所有 Nav2 lifecycle 节点进入 active；② 固定仿真场景连续 10 次从相同起点到目标均返回 action success；③ 非空路径的 frame 与 TF 连通；④ 无 Gazebo 碰撞、无持续 TF extrapolation、无节点崩溃；⑤ 每次的版本、参数、bag 和视频完整可回放。 |
| **通过条件：A1 planner reproduced** | ① 可达目标返回非空 path 且终点误差不超过声明容差；② path 上采样点经同一 costmap footprint 检查无 lethal collision；③ 不可达目标明确失败而不是返回危险直线；④ 重复输入输出在相同地图/参数下可解释且可比较。 |
| **通过条件：A2 integrated/validated** | ① `machine-dog` 明确接受并确认 command；② 新命令可抢占旧命令；③ stale/失联/取消触发停止；④ 10 次固定几何任务到达率达到预先声明阈值；⑤ 航点间轨迹不切入禁区；⑥ 故障注入（状态停止、TF 过期、目标越界）均安全拒绝。完成 A2 才可写 `integrated`；全部验收后才写 `validated`。 |
| **退出/降级条件** | 若无稳定 pose/odom/TF，停止导航接入；若低层无 waypoint API，降级为受限速度 bridge；若无 cancel/watchdog/急停，不接真机；若 path follower 切角，升级为短路径/轨迹跟踪；若 ROS 发行版无法共存，使用进程间 schema 而非强行源码混编。 |
| **不能据此声称** | 不能声称 Lite3 已具备自主导航、动态避障、粗糙地形能力、sim-to-real、学习导航或真机安全；A0/A1 只证明 Nav2 上游可运行和路径接口可审计。 |

### 6.3 路线 B：加入建图、局部避障与地形可通行性

路线 B 应拆成三个独立可退出的子阶段，避免把 SLAM、地形感知和局部规划同时引入后无法归因。

#### B1：定位/建图

| 项目 | 内容 |
|---|---|
| **目标** | 用真实传感器假设替换 stock map/ground-truth pose，得到稳定 `map/odom/base` 关系和可供 planner 使用的环境表示。 |
| **候选** | 2D LiDAR 优先 **SLAM Toolbox**；RGB-D/双目/3D LiDAR 优先 **RTAB-Map ROS**。若已有可靠 LIO，可将其只作为 odom，再由 Nav2 使用静态/局部地图。 |
| **最小任务** | 先运行官方/样例 bag 或仿真；再在固定小场景走闭环轨迹，保存估计轨迹、ground truth（仿真）、地图、TF 和 CPU/内存。 |
| **建议通过条件** | 仿真闭环轨迹 ATE/RMSE 阈值在试验前声明（首轮建议小场景 ≤0.15 m、yaw RMSE ≤5°，仅为项目验收建议）；`map→odom` 不出现未解释跳变；地图更新和 TF 延迟满足局部规划时限；停止/重启后地图和定位可恢复。阈值应在 Lite3 传感器频率确认后冻结。 |
| **退出条件** | 里程计不稳定、传感器同步/外参未知、地图时延持续超预算或回环导致控制不可接受跳变时，停止进入 B2；先解决状态估计。 |

#### B2：局部避障与短路径

| 项目 | 内容 |
|---|---|
| **目标** | 在已验证 pose/map 上加入局部滚动 costmap、静态与动态障碍避让、恢复和碰撞监控。 |
| **候选** | 先用 Nav2 MPPI/RPP/DWB 等官方 controller 作几何基线；视觉局部规划研究用 **ViPlanner**，但先独立验证 `/viplanner/path`，再替换 path follower。 |
| **最小任务** | 固定狭窄通道、盲角、突然放置障碍、局部不可达和传感器失效场景；记录最小障碍距离、重规划时延、速度、急停和恢复结果。 |
| **建议通过条件** | 静态场景 20 次无碰撞；动态障碍场景在预先声明速度/制动距离内停止或绕行；任何 costmap/感知数据超过 stale threshold 时下发零速/取消；路径与执行轨迹的最大横向偏差低于足迹安全裕度。 |
| **退出条件** | planner 的控制频率低于低层需求、感知延迟无法满足制动距离、或 path→waypoint 导致不可控切角时，停止使用航点追踪并改为短轨迹/速度闭环。 |

#### B3：粗糙地形与机器人特定可通行性

| 项目 | 内容 |
|---|---|
| **目标** | 将高程、坡度、台阶、粗糙度、视觉材质和 Lite3 通过经验形成风险层；planner 根据风险选择路线，低层仍负责稳定行走。 |
| **候选** | **Elevation Mapping CuPy** 为几何高程基座；经典 Traversability 作可解释对照；**WVN** 用视觉在线自监督；**LeSTA** 用机器人经验学习；ViPlanner 用语义/深度直接输出局部 path。 |
| **最小任务** | 先运行各自官方 TurtleBot/图片/rosbag/checkpoint smoke；随后在不驱动 Lite3 的离线 bag 上生成 elevation/traversability；最后才接 Nav2 cost layer。 |
| **建议通过条件** | ① 地图连续运行至少 10 分钟，发布率不发生不可恢复的明显衰减；② 风险层含时间戳、置信度和 unknown；③ 人工标注的小型地形集上分类/排序达到预先声明指标；④ planner 不穿越 lethal/unknown 策略禁止区；⑤ 风险层失效时退回保守几何策略。 |
| **退出条件** | ROS 2 分支/容器不稳定、Jetson 长时 FPS 下降、模型在 Lite3 视角明显饱和、或高度图噪声使代价不可信时，模块保持离线研究状态，不进入控制闭环。 |
| **不能据此声称** | 即使地图和路线成功，也不能声称机器人能安全通过所有被判为“可通行”的地形；必须另做 locomotion capability envelope 和真实机器人受控试验。 |

### 6.4 路线 C：加入 VLA/VLN 高层语义规划

| 项目 | 内容 |
|---|---|
| **目标** | 让语言/视觉模型只负责“去哪里、遵守什么规则”，由几何/可通行 planner 负责“如何安全到达”，由 Lite3 RL locomotion 负责“如何稳定运动”。 |
| **上游基座** | 离线评测：**Habitat-Lab/VLN-CE**；高层模型：**NaVILA**；长程开放词汇与几何安全系统参考：**WildOS**；行为规则 cost map 参考：**BehAV**。 |
| **推荐分层** | `language + RGB/video → structured intent / metric subgoal / semantic cost` → 能力与安全验证器 → `Nav2/ViPlanner` → `Path/waypoint/trajectory` → `machine-dog`。VLA 永远不直接写关节/速度话题。 |
| **最小复现任务 C0** | 仅在官方 benchmark 上运行预训练模型评测，保存输入、原始文本/动作、解析结果、轨迹视频和指标；不接机器人。 |
| **最小集成任务 C1** | 把模型输出限定为版本化 JSON schema，例如 `subgoal(dx,dy,dyaw)`、`object_goal(label)`、`constraint(stay_on, pavement)`；所有输出先投影到当前 free/traversable map。 |
| **最小闭环任务 C2** | 在仿真中执行语言任务；VLA 低频更新，Nav2/ViPlanner 高频避障。模型等待期间保持现有安全轨迹或停止，不允许继续执行过期语言动作。 |
| **所需环境** | NaVILA 训练/评测需 8B 模型、CUDA、legacy Habitat/VLN-CE 和场景数据；WildOS 需 Jazzy、GPU、DLIO、Elevation Mapping、Nav2；建议与路线 A/B 通过网络服务隔离。 |
| **预期产物** | 模型/数据许可证清单、checkpoint SHA、prompt/schema 版本、每步原始输出、拒绝/修正原因、metric subgoal、planner result、执行轨迹、语义成功和安全指标。 |
| **建议通过条件** | ① 解析器对测试集输出要么产生合法 schema，要么安全拒绝，不能静默猜测；② 100% 被执行 subgoal 在当时地图中通过能力/碰撞/范围检查；③ 无任何路径绕过 planner 直达低层；④ 在固定语言任务集上达到预先声明成功率，并优于“随机/仅几何”适当基线；⑤ 高层超时、模型断开或不确定性过高时安全停止。 |
| **退出条件** | 旧 Habitat 无法固定、数据许可不足、模型经常生成不可达/左右错误动作、推理延迟超预算、或 semantic gain 不超过几何基线时，保留离线研究，不进入 Lite3 控制。 |
| **不能据此声称** | 不能声称端到端 VLA 控制、通用具身智能、开放世界泛化或真机语言导航安全；分层系统成功只证明指定任务和模型版本下的受约束高层规划。 |

### 6.5 三条路线的推荐先后关系

```text
路线 A：Nav2 stock → planner-only Path → Lite3 interface contract
                  │
                  ├─ 路线 B1：SLAM / state estimation
                  ├─ 路线 B2：local avoidance / ViPlanner
                  └─ 路线 B3：elevation + traversability
                                      │
                                      └─ 路线 C：VLA/VLN structured intent
```

路线 C 不应绕过 A/B。即使博士主题最终聚焦 VLA、世界模型或语义导航，几何闭环仍是安全基线、故障回退和归因工具。

---
## 7. 第一复现对象（Nav2）的执行准备

### 7.1 固定上游与复现策略

| 项目 | 固定内容 |
|---|---|
| Canonical 仓库 | [ros-navigation/navigation2](https://github.com/ros-navigation/navigation2) |
| 当前默认分支审计快照 | `main`；[`db906947171abe170c25181347be9bc7bcbc1a75`](https://github.com/ros-navigation/navigation2/commit/db906947171abe170c25181347be9bc7bcbc1a75)，核验日期 2026-07-23 |
| 第一轮实际运行版本 | **ROS 2 Jazzy 官方二进制发行包**，而不是上述 `main` 源码。运行时用 `apt-cache policy` 固定每个包的确切 Debian 版本；当前审计 SHA 只说明上游现状，不能冒充二进制对应 commit。 |
| 推荐主机 | Ubuntu 24.04 amd64 的干净系统、虚拟机或容器；GUI 仿真需可用 OpenGL/X11/Wayland。若现有 Lite3 栈固定 Foxy，先隔离，不在同一 shell 混 source。 |
| 代码边界 | 官方二进制、上游 clone、BT XML、planner/controller plugin、仿真世界在完成上游 smoke 前全部只读。证据脚本、参数快照和后续 bridge 放在独立目录。 |

### 7.2 官方安装与最小 smoke 命令

以下命令来自 Nav2 官方安装/Getting Started 路径；本报告没有执行：

```bash
# 1. 确认 ROS 发行版环境
source /opt/ros/jazzy/setup.bash
export ROS_DISTRO=jazzy

# 2. 安装 Nav2、bringup 和最小 TurtleBot 仿真资源
sudo apt update
sudo apt install \
  ros-$ROS_DISTRO-navigation2 \
  ros-$ROS_DISTRO-nav2-bringup \
  'ros-'$ROS_DISTRO'-nav2-minimal-tb*'

# 3. 官方 stock simulation smoke
ros2 launch nav2_bringup tb3_simulation_launch.py headless:=False
```

启动后按官方教程在 RViz 设置初始位姿（若场景未自动初始化）和 `Nav2 Goal`。第一轮不改参数，不替换 planner/controller，不加入 Lite3 模型。

### 7.3 执行前版本与环境取证

```bash
mkdir -p evidence/nav2-stock/{logs,bags,video,manifests}

{
  date --iso-8601=seconds
  uname -a
  lsb_release -a || cat /etc/os-release
  printenv | sort
  ros2 doctor --report
  apt-cache policy \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-nav2-minimal-tb3-sim
  dpkg-query -W 'ros-jazzy-nav2*' 'ros-jazzy-navigation2' 2>/dev/null
} | tee evidence/nav2-stock/manifests/environment_manifest.txt
```

包名可能随官方 minimal-TB packaging 略有差异；实际安装后应以 `apt-cache search nav2-minimal-tb` 和 `dpkg-query` 的真实结果为准，不能在报告中补写不存在的包。

### 7.4 模型、数据与资源需求

| 项目 | 结论 |
|---|---|
| 模型 checkpoint | **无**。Nav2 stock demo 不依赖学习模型。 |
| 数据集 | **无外部数据集**。所需地图、机器人模型和 Gazebo 世界由已安装的 bringup/minimal TB 仿真包提供。 |
| Docker/conda | Nav2 有容器/devcontainer 路径，但官方 Getting Started 的二进制主机安装更直接。第一轮只选一种环境，避免双重变量。 |
| CUDA/GPU | 算法不要求 CUDA。RViz/Gazebo GUI 需要图形加速或软件渲染；headless 可降低图形要求。 |
| 官方精确 RAM/磁盘下限 | **未找到**。 |
| 项目预算估计（非上游保证） | 4 个 CPU 核心、8 GB RAM 可作为最低 smoke 预算；建议 8 核/16 GB RAM；新环境预留 15–25 GB 磁盘；无独立显卡也可 headless。实际峰值必须从 `/usr/bin/time -v`、`pidstat`、`nvidia-smi`（如适用）和磁盘清单实测。 |

### 7.5 应保存的运行证据

1. **控制台与 ROS 日志**：完整 launch stdout/stderr，`~/.ros/log`，生命周期状态变化和 action result。
2. **版本证据**：OS、ROS、RMW、Gazebo、Nav2 Debian 版本，全部参数文件的 SHA256。
3. **ROS bag**：至少记录 `/tf`、`/tf_static`、`/map`、`/odom`、`/scan`、实际 global/local plan topic、`/cmd_vel` 或 `TwistStamped` 输出、goal/action status；确切 topic 先由 `ros2 topic list -t` 获取。
4. **视频**：RViz 和 Gazebo 同步录屏，包含起点、目标、路径、costmap、执行和最终状态。
5. **指标文件**：起终点、action duration、路径长度、执行轨迹长度、到达误差、最小障碍距离、碰撞数、recovery 次数、CPU/RAM 峰值。
6. **复现脚本**：只包含启动、取证、goal 注入和指标计算，不修改上游源码。

建议的 bag 命令应在确认真实 topic 后生成，例如：

```bash
ros2 topic list -t | tee evidence/nav2-stock/manifests/topics.txt
ros2 action list -t | tee evidence/nav2-stock/manifests/actions.txt

# 用实际发现的 topic 替换下列集合；不要静默忽略不存在的 topic
ros2 bag record -o evidence/nav2-stock/bags/run_001 \
  /tf /tf_static /map /odom /scan /cmd_vel
```

### 7.6 最小成功标准

一个 run 只有同时满足以下条件才计为成功：

- launch 进程未崩溃，Nav2 lifecycle 节点均 active；
- goal 被 action server 接收；
- planner 返回非空且 frame 有效的路径；
- robot 在规定超时内到达官方 goal tolerance；
- action result 为 succeeded，而不是仅凭画面判断；
- Gazebo contact/位置证据中无碰撞；
- bag、日志、视频和 manifest 均存在且可读取。

完成 10 个一致配置的成功 run 后，Nav2 stock 项目可标记 `reproduced`。这不使任何 Lite3 能力变成 `reproduced`、`integrated` 或 `validated`。

### 7.7 常见失败点与诊断顺序

| 失败症状 | 首先检查 | 不应立即采取的做法 |
|---|---|---|
| RViz 有地图但机器人不动 | lifecycle、goal action、`/cmd_vel`、sim controller、`use_sim_time` | 不先修改 controller plugin 源码。 |
| “No transform”/costmap 空 | `map→odom→base_link→sensor` TF、时间戳、frame 名、静态外参 | 不用静态假 TF 掩盖真实状态估计缺失。 |
| planner 无路径 | 起/终点是否在 free space、footprint/inflation、地图分辨率、planner 日志 | 不把 lethal/unknown 全部改成 free。 |
| 路径有但 controller 失败 | local costmap、controller frequency、速度约束、initial pose、进度 checker | 不先增大速度或关闭碰撞检查。 |
| GUI 卡顿/仿真慢 | real-time factor、CPU/RAM、OpenGL、headless 模式 | 不把性能不足误判为 planner 算法失败。 |
| 重复 run 结果漂移 | 初始 pose、仿真 reset、随机种子、时间源、残留 lifecycle/process | 不在未重置环境中混合统计。 |
| DDS 发现或 topic 丢失 | `ROS_DOMAIN_ID`、RMW、网络、重复 ROS 环境 source | 不同时 source Foxy/Jazzy workspace。 |
| stale 命令持续输出 | controller stop/cancel、velocity smoother、watchdog、bag 时间 | 真机前不得绕过 stale/stop 测试。 |

### 7.8 接入 Lite3 前保持只读的边界

在 Nav2 stock `reproduced` 前，以下内容保持只读：

- `/opt/ros/jazzy/share/nav2_*` 和 `/opt/ros/jazzy/lib/nav2_*`；
- upstream `navigation2` clone 的所有源码；
- 官方 BT XML、planner/controller 参数、TurtleBot URDF 与 Gazebo world；
- 官方 action/message definitions；
- 原始日志、bag、视频和 manifest。

任何项目自定义都应新增而不是覆盖：独立参数 overlay、独立 bridge package、独立 Lite3 URDF/footprint、独立 acceptance-test 配置。第一次修改上游前必须保留 clean tag/SHA、patch 文件和可回到 stock smoke 的命令。

---
## 8. Lite3 运动控制接口待确认清单

### 8.1 已知但不能外推的公开信息

Deep Robotics 的公开 [Lite3_ROS](https://github.com/DeepRoboticsLab/Lite3_ROS)（`ros2-foxy`）把运动主机的腿式里程计、IMU、关节状态转成 ROS 2 topic，并订阅 `/cmd_vel` (`geometry_msgs/Twist`)；它没有公开 waypoint/trajectory action。公开 [Lite3_MotionSDK](https://github.com/DeepRoboticsLab/Lite3_MotionSDK) 是更低层的 12 关节 `pos/vel/kp/kd/feedforward torque` 接口，并说明 SDK 指令超过 1 秒未到时底层收回控制权进入阻尼保护。公开 [Lite3_rl_deploy](https://github.com/DeepRoboticsLab/Lite3_rl_deploy) 展示键盘/手柄驱动 RL 策略和 sim-to-sim/sim-to-real结构。

这些信息只能说明厂商公开示例的接口，不足以推断当前 `machine-dog` 仓库的策略、归一化、频率、命令队列和安全行为。正式集成前必须由 `machine-dog` 维护者以源码、配置和实际测试给出以下答案。

### 8.2 必须冻结的接口字段

| 组别 | 必须确认的具体问题 | 需要保存的证据 | 未确认时的后果 |
|---|---|---|---|
| **命令类型** | 控制器实际接受：`Twist`、相对 waypoint、绝对 pose、短路径、带时间轨迹、技能 token，还是关节/策略 action？是否同时支持多种入口？ | 公开/项目内 API 定义、消息/函数签名、最小调用示例、单元测试 | 无法确定 Nav2/ViPlanner 输出应接在哪一层；不得开始 bridge。 |
| **命令版本** | 接口 schema/version、序列化格式、字段默认值、向后兼容策略是什么？ | IDL/protobuf/ROS msg、版本号、commit SHA | 上游或 checkpoint 更新后可能静默改变行为。 |
| **控制权与仲裁** | App、遥控器、ROS、RL policy、SDK、急停谁优先？进入/退出自动模式的状态机和前置条件是什么？ | 状态机图、优先级表、切换日志 | 多源命令竞争可能导致不可预测运动。 |
| **速度/航点/轨迹语义** | `vx,vy,wz` 是期望机体速度、步态参考还是已经限幅的执行值？Waypoint 是直线目标、heading target 还是由内部 planner 跟踪？轨迹点是否含时间？ | 源码注释、参数、输入输出回放 | 同名字段可能具有不同动态意义；错误适配会导致振荡或切角。 |
| **指令坐标系** | 命令使用 `base_link`、质心、IMU、`odom`、`map` 还是自定义 frame？x/y/z 正方向、右手系、yaw 正方向和角度单位？ | TF/坐标图、静态外参、数值测试（前/左/逆时针） | 最严重可导致左右、前后或角速度符号反转。 |
| **状态估计坐标系** | pose、velocity、orientation 分别在哪个 frame；`odom` 是否连续、`map` 是否允许跳变；四元数顺序；重置/漂移语义？ | topic/API 定义、TF tree、重置试验、ground-truth 对比 | planner 无法正确闭环；相对航点会累积漂移，绝对航点会在跳变时失稳。 |
| **时间源与时间戳** | ROS time、monotonic clock、motion-host clock 如何同步；消息是否带采样时刻或接收时刻；最大 clock skew？ | NTP/PTP/时钟设计、bag 时序、延迟测量 | 无法判断观测和命令是否过期，影响碰撞与状态估计。 |
| **命令频率** | 最低、标称、最高更新率；低于最低频率时插值、保持、清零还是进入保护？ | 频率扫描测试、watchdog 源码/配置 | 导航侧可能以过低频率驱动低层，或用高频洪泛队列。 |
| **端到端延迟/抖动** | 从导航产生命令到策略读入、再到机器人状态变化的 median/P95/P99；允许最大抖动和丢包率？ | 统一时钟的 trace、network capture、实测统计 | 无法设置预测 horizon、制动距离和 stale threshold。 |
| **队列与抢占** | 新 waypoint 是否覆盖旧目标；是否有 queue；取消/clear queue API；重复 command_id 是否幂等？ | API 测试与日志 | 旧目标可能在新目标后继续执行，造成危险回摆。 |
| **航点容差** | 到达判定的 xy/z/yaw 容差；是否要求停稳；可否只过点不停车；超时如何处理？ | 参数和固定航点测试 | 导航与控制层对“完成”的判断不一致，出现无限重发或提前完成。 |
| **路径跟踪行为** | 若输入 path/waypoint，lookahead、插值、切角、倒退、原地旋转、侧移规则是什么？ | 直角、S 弯、窄通道和回头路径测试 | planner 的无碰撞路径不能保证执行轨迹无碰撞。 |
| **最大线速度/角速度** | `vx/vy/wz` 上下限；速度组合的联合约束；不同步态/地形下限值是否变化？ | 参数表、饱和测试、策略训练范围 | Nav2/trajectory planner 的动态模型会与低层不一致。 |
| **加速度/jerk/转向约束** | 最大线/角加速度、减速度、jerk、最小转弯半径；能否原地旋转和侧向走？ | step/ramp 输入测试、配置 | 局部 planner 可能生成低层无法跟踪的速度变化。 |
| **步态与模式** | 支持哪些 gait；导航是否可请求 gait/height；模式切换需要停稳吗；切换延迟和失败行为？ | 状态机、模式 topic/API、测试 | 动态地形能力和安全包络无法建模。 |
| **急停** | 软停、硬急停、App 急停、网络失联、进程崩溃分别做什么；如何复位；是否保持关节阻尼？ | 安全手册、代码、故障注入视频/日志 | 任何真机导航前的硬阻塞项。 |
| **watchdog/stale** | 最后有效命令超过多少毫秒被判 stale；是零速、站立、阻尼还是释放；公开 MotionSDK 的“1 秒”是否适用于当前 RL 控制路径？ | 当前控制器源码/配置和丢包试验 | 不能直接沿用厂商 SDK 数值；错误假设可能让机器人持续运动。 |
| **失联与重连** | UDP/TCP/ROS DDS 断开、motion host 重启、导航进程重启后是否自动恢复控制；是否需要人工重新授权？ | 网络故障注入、状态转换记录 | 自动重连可能在旧目标下恢复运动。 |
| **反馈与错误码** | 是否返回 accepted/active/reached/rejected；tracking error、fall/slip/contact、policy fault、temperature、电池、通信状态？ | 消息定义、错误码表、日志样例 | 导航层只能猜测是否到达或失败，无法安全 recovery。 |
| **碰撞责任** | 低层是否自带 obstacle avoidance；若有，使用什么传感器/范围；与导航 costmap 冲突时谁优先？ | 架构说明与障碍测试 | 双重避障可能振荡；两边都不负责则碰撞。 |
| **地形适应范围** | 已训练/验证的坡度、台阶高度、沟宽、粗糙度、摩擦、负障碍、楼梯、草地；是作者报告还是本项目验证？ | 训练配置、实验协议、失败边界 | 不能把“RL rough terrain”笼统标签转成 planner traversability threshold。 |
| **机器人几何** | navigation footprint、最大外廓、站立/转身/步态变化后的动态 footprint、传感器盲区？ | URDF/CAD、实测尺寸、不同姿态包络 | costmap footprint 过小导致碰撞，过大导致假不可达。 |
| **策略观测输入** | IMU、关节、历史、command、height scan、depth/RGB、contact 等具体顺序、单位、归一化、stack 长度和更新率？ | observation schema、训练/部署 config | checkpoint 不能可靠加载；导航命令可能进入错误索引或量纲。 |
| **策略动作输出** | action 顺序、缩放、clipping、默认关节位、PD 参数、decimation；是否含 residual/phase？ | export metadata、训练 config、部署代码 | 同一个 checkpoint 在仿真和真机可能产生不同关节目标。 |
| **checkpoint 身份** | 模型文件 SHA256、训练 run、代码 commit、env/agent YAML、随机种子、导出工具版本、ONNX opset 和运行时版本？ | 不可变 manifest 和模型元数据 | 无法复现实验或追踪接口变化。 |
| **策略命令训练范围** | 训练时 command distribution 的 `vx/vy/wz` 范围、deadband、curriculum；是否训练 waypoint/heading 任务？ | 训练 config 和统计 | 不能向策略发送超出分布的导航命令。 |
| **仿真—真机一致性** | 两端是否调用同一 policy runner、同一 observation/action schema、同一控制频率和坐标系；仿真传感器噪声/延迟如何建模？ | 接口 diff、自动对比测试、sim-to-sim 与 sim-to-real 日志 | 仿真集成成功不能外推真机。 |
| **状态重置** | episode reset、跌倒恢复、里程计 reset、重新站立是否改变 frame 或 command 状态？ | reset 测试和状态机 | 导航可能在重置后继续追旧世界坐标目标。 |
| **算力与部署位置** | policy 在 motion host、Jetson 还是外部 PC；CPU/GPU 占用、实时优先级、网络带宽；导航与策略是否争用资源？ | profile、部署图、性能日志 | 资源争用会改变控制周期和传感器延迟。 |
| **日志与可观测性** | 能否同步记录 raw observation、normalized observation、command、action、joint target、state estimate 和 safety state？ | logging schema、bag/file demo | 无法定位导航错误还是控制策略错误。 |

### 8.3 正式集成的最低准入条件

正式编写 bridge 前，至少要交付一份机器可读 `machine-dog-control-interface.yaml`，包含：

```yaml
interface_version: "..."
controller_commit: "..."
checkpoint_sha256: "..."
command:
  type: twist | waypoint | path | trajectory
  frame_id: "..."
  units: "..."
  nominal_rate_hz: ...
  min_rate_hz: ...
  stale_timeout_ms: ...
  limits: {vx: [..., ...], vy: [..., ...], wz: [..., ...], ax: ..., aw: ...}
state:
  pose_frame: "..."
  velocity_frame: "..."
  topics_or_api: {...}
completion:
  xy_tolerance_m: ...
  yaw_tolerance_rad: ...
  settle_time_s: ...
safety:
  cancel_api: "..."
  emergency_stop: "..."
  command_loss_behavior: "..."
  collision_owner: "navigation | controller | both-with-arbitration"
sim_real:
  identical_schema: true | false
  known_differences: [...]
```

任何 `...` 未填、没有来源或没有最小测试时，接口状态应保持 `unknown`，不得由导航仓库自行补默认值。

---
## 9. 证据缺口与下一步

### 9.1 本轮仍未获得的项目内部证据

本轮没有获得 `machine-dog`、`machine-dog-nav` 的可访问源码、commit、配置、checkpoint 或运行日志，因此以下内容**未检查**：

- `machine-dog` 的真实命令入口、坐标、频率、限幅、watchdog、状态机和反馈；
- 当前 RL policy 的 observation/action schema、训练范围、checkpoint SHA 和导出版本；
- Lite3 仿真后端、真机 driver 与策略 runner 是否共用同一接口；
- `machine-dog-nav` 是否已经存在 ROS 2 workspace、消息、TF、URDF、传感器 driver 或测试框架；
- 实际机器人上的 LiDAR/RGB-D/相机型号、安装位姿、同步方式、算力平台和网络；
- 真机急停、遥控器仲裁、实验场地和安全审批流程。

因此，本报告对“几何航点”的推荐是**条件化架构建议**，不是对现有控制器能力的事实陈述。

### 9.2 下载完整仓库后才能确认的内容

| 缺口 | 为什么网页审计不足 | 下一步证据 |
|---|---|---|
| 每个候选的完整依赖许可证 | README/根 LICENSE 不能覆盖 vendored library、submodule、模型和数据 | 对固定 SHA 递归 clone；生成 submodule 清单、`licensee/scancode` 报告和 SBOM；人工审查冲突。 |
| Nav2 混合许可证的精确复用边界 | 各 ROS package 的许可证不同 | 对计划复用的 package 逐一记录 `package.xml` 和 LICENSE；不要复制不需要的包。 |
| FAR/TARE/Agile 的作者许可 | 仓库可见但无根 LICENSE | 联系作者取得书面许可证或新增 OSI 许可证；在此之前只读研究、禁止合并/再发布。 |
| 官方命令在固定 SHA 是否仍一致 | README 可能针对分支其他时点或外部仓库 | clone 固定 SHA，保存 README/launch/package lock；逐命令核对文件存在性。 |
| ViPlanner checkpoint/config 的文件哈希和许可 | 下载托管在外部存储，仓库未统一给出所有哈希 | 下载后计算 SHA256，记录来源、时间、大小、模型许可和 config 对应关系。 |
| NaVILA/WildOS 的模型和数据依赖许可 | 代码 Apache-2.0 不自动覆盖 Llama/VILA、SigLIP/RADIO、MP3D/视频等 | 建立 model/data card 与逐项用途许可矩阵。 |
| Quad-SDK 第三方求解器条件 | Quad 代码 MIT，但 HSL 获取有独立条件 | 保存 HSL 版本、下载授权、IPOPT/solver 许可和可再分发限制。 |
| ROS 2 分支实际覆盖 | Elevation Mapping 等项目 README 与 branch/issue 状态不完全一致 | checkout ROS 2 分支，列出可编译 package、ROS1 残留和示例所需外部组件。 |

### 9.3 必须实际运行才能确认的内容

- 安装成功率、下载体积、构建时间、峰值 RAM/VRAM、CPU/GPU 占用和磁盘需求；
- 官方 smoke/demo 是否能在项目硬件、驱动和网络环境启动；
- issue 中的错误是否仍能在固定版本复现，或已有未发布修复；
- ROS topic/action 的真实名称、QoS、频率、延迟和 TF 连通性；
- checkpoint 输出、导航成功率、路径质量、碰撞、恢复和长时稳定性；
- 第三方复现是否真正在相同 commit/资产/命令下成功；issue 中一句“works”不够；
- Nav2/ViPlanner/FAR 的 path 经 Lite3 follower 后是否切角或违背动态约束；
- Elevation Mapping 在目标 Jetson/传感器组合上的长期发布率；
- VLA/VLN 模型的实际显存、推理延迟、动作合法率与方向/距离错误率；
- 仿真到真机的接口一致性、网络失联和安全行为。

### 9.4 必须由 Lite3 团队或硬件实验确认的内容

- 第 8 节全部控制接口字段；
- 足迹和动态外廓、坡度/台阶/沟宽等 locomotion capability envelope；
- 传感器内外参、时间同步与遮挡；
- 运动主机是否允许外部自动控制、可用控制模式和责任边界；
- 急停、失联、摔倒恢复和实验场地安全程序；
- `machine-dog` checkpoint 对真实 Lite3 型号/固件/关节参数的适配；
- 研究机构对第三方模型、数据和代码许可证的合规要求。

### 9.5 下一轮优先级与预期状态迁移

| 优先级 | 工作包 | 输入 | 预期输出 | 最多可达到的状态 |
|---:|---|---|---|---|
| P0 | **冻结 Lite3 控制接口** | `machine-dog` 源码、checkpoint、仿真/真机 API 维护者 | 第 8.3 节 YAML、时序图、限制表、最小 mock client、故障行为记录 | `surveyed`；若接口测试实际运行可将控制接口本身记为 `reproduced`，但导航仍不是 |
| P0 | **冻结平台/传感器清单** | Lite3 型号、计算机、OS、ROS、LiDAR/相机、外参 | hardware/software manifest、TF 设计、数据带宽和时钟方案 | `surveyed` |
| P0 | **许可证隔离** | FAR/TARE/Agile、模型/数据依赖 | allow/deny/quarantine 清单；无许可证项目不进入主仓库 | `surveyed` |
| P1 | **Nav2 stock smoke** | 干净 Jazzy 环境 | 10-run 日志/bag/video/metrics、包版本锁 | Nav2 可到 `reproduced` |
| P1 | **Nav2 planner-only smoke** | 固定地图和 goal set | `ComputePathToPose` 结果、碰撞审计、不可达测试 | Nav2 planner 可到 `reproduced` |
| P1 | **ViPlanner 独立 smoke** | 官方 checkpoint/config、样例或 Isaac demo | 模型输出、`nav_msgs/Path`、资源与失败记录 | ViPlanner 可到 `reproduced` |
| P1/P2 | **Quad-SDK 独立 smoke** | 官方 Jazzy/HSL 环境 | Gazebo/规划/控制证据；不接 Lite3 | Quad-SDK 可到 `reproduced` |
| P2 | **Path/waypoint bridge mock** | 已冻结控制 schema、仿真 mock | frame/expiry/preempt/cancel/stale 单元与故障测试 | bridge 可到 `reproduced`；尚未 `integrated` |
| P2 | **Lite3 仿真最小闭环** | Nav2 path + bridge + `machine-dog` 仿真 | 固定 waypoint 场景、轨迹、失败注入 | 完成接线后 `integrated`；通过验收后 `validated` |
| P3 | **SLAM/局部避障/地形** | 已稳定的 A 路线 | 分层模块证据和逐级验收 | 各模块独立迁移状态 |
| P4 | **VLA/VLN 高层** | 已 validated 的几何安全闭环 | 结构化意图、planner 验证、semantic benchmark | 先离线 `reproduced`，后续再集成 |

### 9.6 条件化决策树

```text
machine-dog 是否有稳定、可抢占、有 watchdog 的 waypoint/path API？
├─ 是：Nav2/ViPlanner Path → 几何航点，作为第一项目接口
└─ 否：是否有稳定 Twist API？
   ├─ 是：Nav2 Path → 安全 follower → Twist；项目内部仍保留 Path/waypoint 抽象
   └─ 否：停止导航集成，先完成控制接口

第一研究目标是否必须包含三维粗糙地形动态可行性？
├─ 否：Nav2 → mapping/avoidance → traversability，按 A/B 路线推进
└─ 是：Nav2 仍作基线，同时独立复现 ViPlanner 与 Quad-SDK；不要跳过几何基线

是否必须马上做语言导航？
├─ 否：延后到 A/B 有稳定安全闭环后
└─ 是：仅做 Habitat/NaVILA 离线评测和结构化 subgoal，不接真机
```

---
## 10. 来源附录

### 10.1 证据解释

- 下列链接均指向原始论文、作者/机构项目页、canonical 仓库、官方文档或具体 issue；未使用搜索结果页作为关键结论来源。
- 论文中的性能、SOTA、首次、优于等均只应理解为**作者报告**。本项目没有独立运行这些实验。
- GitHub commit、默认分支和 issue 状态核验日期为 **2026-07-23**；上游随后可能变化。
- 本报告记录的命令均来自官方 README/文档；状态仍是 `surveyed`，不是运行证明。

### 10.2 Lite3 官方接口与运动控制线索

| 来源 | 用途 |
|---|---|
| [DeepRoboticsLab/Lite3_ROS](https://github.com/DeepRoboticsLab/Lite3_ROS) | 官方 ROS 2 Foxy UDP bridge；公开 `/leg_odom`、`/leg_odom2`、IMU、关节状态与 `/cmd_vel`。 |
| [Lite3_ROS README 固定分支](https://github.com/DeepRoboticsLab/Lite3_ROS/tree/ros2-foxy) | 公开 topic、速度方向和 10 Hz 示例命令。 |
| [DeepRoboticsLab/Lite3_MotionSDK](https://github.com/DeepRoboticsLab/Lite3_MotionSDK) | 低层关节 SDK、PD/前馈参数和超时阻尼说明；不是导航接口。 |
| [DeepRoboticsLab/rl_training](https://github.com/DeepRoboticsLab/rl_training) | 基于 Isaac Lab 的当前 Lite3 RL 训练入口、模型导出与元数据线索。 |
| [DeepRoboticsLab/Lite3_rl_deploy](https://github.com/DeepRoboticsLab/Lite3_rl_deploy) | 官方 sim-to-sim/sim-to-real RL 部署、state machine、keyboard/gamepad command 与 ONNX 运行路径。 |

### 10.3 几何导航、SLAM 与探索

| 候选 | 原始论文/项目页 | Canonical 仓库与固定快照 | 官方运行/接口证据 | 许可证/维护证据 |
|---|---|---|---|---|
| Nav2 | [The Marathon 2](https://arxiv.org/abs/2003.00368)；[Nav2 官方站](https://docs.nav2.org/) | [仓库](https://github.com/ros-navigation/navigation2)；[固定 commit](https://github.com/ros-navigation/navigation2/commit/db906947171abe170c25181347be9bc7bcbc1a75) | [Getting Started](https://docs.nav2.org/getting_started/index.html)；[ComputePathToPose action](https://api.nav2.org/actions/jazzy/computepathtopose.html)；[自定义 controller plugin](https://docs.nav2.org/plugin_tutorials/docs/writing_new_nav2controller_plugin.html) | [根许可证](https://github.com/ros-navigation/navigation2/blob/main/LICENSE)；实际复用须核验各 package 的 `package.xml`/LICENSE；[issues](https://github.com/ros-navigation/navigation2/issues) |
| SLAM Toolbox | [JOSS 论文](https://joss.theoj.org/papers/10.21105/joss.02783) | [仓库](https://github.com/SteveMacenski/slam_toolbox)；[固定 commit](https://github.com/SteveMacenski/slam_toolbox/commit/eee0cd5e4a161bb10f8334b5420c93876b31ca99) | [README](https://github.com/SteveMacenski/slam_toolbox/blob/ros2/README.md)；[launch files](https://github.com/SteveMacenski/slam_toolbox/tree/ros2/launch) | [LGPL-2.1](https://github.com/SteveMacenski/slam_toolbox/blob/ros2/LICENSE)；[#662](https://github.com/SteveMacenski/slam_toolbox/issues/662)、[#827](https://github.com/SteveMacenski/slam_toolbox/issues/827)、[#867](https://github.com/SteveMacenski/slam_toolbox/issues/867) |
| RTAB-Map ROS | [Journal of Field Robotics 论文](https://doi.org/10.1002/rob.21831)；[RTAB-Map](https://introlab.github.io/rtabmap/) | [ROS 仓库](https://github.com/introlab/rtabmap_ros)；[固定 commit](https://github.com/introlab/rtabmap_ros/commit/2eef2b3231090f0a5cc2e092fd993166157cdd64) | [ROS 2 README](https://github.com/introlab/rtabmap_ros/blob/ros2/README.md)；[examples](https://github.com/introlab/rtabmap_ros/tree/ros2/rtabmap_examples/launch)；[demos](https://github.com/introlab/rtabmap_ros/tree/ros2/rtabmap_demos) | [BSD-3-Clause](https://github.com/introlab/rtabmap_ros/blob/ros2/LICENSE)；[#1438](https://github.com/introlab/rtabmap_ros/issues/1438)、[#1436](https://github.com/introlab/rtabmap_ros/issues/1436) |
| FAR Planner | [论文](https://arxiv.org/abs/2110.09460)；[官方项目页](https://www.cmu-exploration.com/far-planner) | [仓库](https://github.com/MichaelFYang/far_planner)；[固定 commit](https://github.com/MichaelFYang/far_planner/commit/2799b6964c141cacd1c32a14b19bc7abffbe0e52) | [README/官方 launch 步骤](https://github.com/MichaelFYang/far_planner/blob/melodic-noetic/README.md)；[AEDE](https://github.com/jizhang-cmu/ground_based_autonomy_basic) | **根 LICENSE 未找到**；[#17](https://github.com/MichaelFYang/far_planner/issues/17)、[#14](https://github.com/MichaelFYang/far_planner/issues/14)、[#10](https://github.com/MichaelFYang/far_planner/issues/10) |
| TARE | [RSS 2021 论文](https://www.roboticsproceedings.org/rss17/p018.html)；[Science Robotics 扩展](https://doi.org/10.1126/scirobotics.adf0970) | [仓库](https://github.com/caochao39/tare_planner)；[固定 commit](https://github.com/caochao39/tare_planner/commit/44500592b86138257273e0cab264e6a847ccefc7) | [README](https://github.com/caochao39/tare_planner/blob/melodic-noetic/README.md)；[AEDE](https://github.com/jizhang-cmu/ground_based_autonomy_basic) | **根 LICENSE 未找到**；[#21](https://github.com/caochao39/tare_planner/issues/21)、[#28](https://github.com/caochao39/tare_planner/issues/28)、[#29](https://github.com/caochao39/tare_planner/issues/29) |

### 10.4 四足专用规划、局部规划与可通行性

| 候选 | 原始论文/项目页 | Canonical 仓库与固定快照 | 官方运行/接口证据 | 许可证/维护证据 |
|---|---|---|---|---|
| Quad-SDK | [官方论文与文档入口](https://robomechanics.github.io/quad-sdk/latest/)；[Fast Global Motion Planning](https://www.andrew.cmu.edu/user/amj1/papers/IROS2020_Fast_Global_Motion_Planning.pdf) | [仓库](https://github.com/robomechanics/quad-sdk)；[固定 commit](https://github.com/robomechanics/quad-sdk/commit/50b58ce8f248ff8995270eae3fa0488c91eeddd4) | [ROS 2 文档](https://robomechanics.github.io/quad-sdk/ros2/)；[安装](https://robomechanics.github.io/quad-sdk/ros2/getting-started/installation/)；[Quick Start](https://robomechanics.github.io/quad-sdk/latest/tutorials/first-run/) | [MIT](https://github.com/robomechanics/quad-sdk/blob/main/LICENSE)；[#443](https://github.com/robomechanics/quad-sdk/issues/443)、[#425](https://github.com/robomechanics/quad-sdk/issues/425)、[#450](https://github.com/robomechanics/quad-sdk/issues/450) |
| Agile Navigation | [论文](https://arxiv.org/abs/2403.10101)；[作者项目页](https://zwt006.github.io/posts/AgileNav/) | [仓库](https://github.com/ZWT006/agile_navigation)；[固定 commit](https://github.com/ZWT006/agile_navigation/commit/bc63aa2ead71e224a4cc68fd7aeac3ac982f6426) | [README](https://github.com/ZWT006/agile_navigation/blob/release/README.md)；[依赖的 legged_control fork](https://github.com/ZWT006/legged_control) | **根 LICENSE 未找到**；无稳定 release/活跃 issue 证据 |
| ViPlanner | [论文](https://arxiv.org/abs/2310.00982)；[项目页](https://leggedrobotics.github.io/viplanner.github.io/) | [仓库](https://github.com/leggedrobotics/viplanner)；[固定 commit](https://github.com/leggedrobotics/viplanner/commit/6fcf3c60f6fa3b28b3a11af054d6033825923789) | [ROS README](https://github.com/leggedrobotics/viplanner/blob/main/ros/README.md)；[固定 commit 的 ROS 包目录](https://github.com/leggedrobotics/viplanner/tree/6fcf3c60f6fa3b28b3a11af054d6033825923789/ros)；[独立 pathFollower 源码](https://github.com/leggedrobotics/viplanner/blob/6fcf3c60f6fa3b28b3a11af054d6033825923789/ros/pathFollower/src/pathFollower.cpp) | [BSD-3-Clause](https://github.com/leggedrobotics/viplanner/blob/main/LICENSE)；[#101](https://github.com/leggedrobotics/viplanner/issues/101)、[#105](https://github.com/leggedrobotics/viplanner/issues/105)、[#112](https://github.com/leggedrobotics/viplanner/issues/112) |
| Elevation Mapping CuPy | [IROS 2022 论文](https://arxiv.org/abs/2204.12876)；[MEM](https://arxiv.org/abs/2309.16818) | [仓库](https://github.com/leggedrobotics/elevation_mapping_cupy)；[固定 commit](https://github.com/leggedrobotics/elevation_mapping_cupy/commit/20a8a26b67a995b43eb44c23568854d1fed82a52) | [官方文档](https://leggedrobotics.github.io/elevation_mapping_cupy/)；[README quick instructions](https://github.com/leggedrobotics/elevation_mapping_cupy/blob/main/README.md) | [MIT](https://github.com/leggedrobotics/elevation_mapping_cupy/blob/main/LICENSE)；[#137](https://github.com/leggedrobotics/elevation_mapping_cupy/issues/137)、[#141](https://github.com/leggedrobotics/elevation_mapping_cupy/issues/141)、[#139](https://github.com/leggedrobotics/elevation_mapping_cupy/issues/139) |
| Traversability Estimation | [项目 README 中引用的几何 traversability 工作](https://github.com/leggedrobotics/traversability_estimation) | [仓库](https://github.com/leggedrobotics/traversability_estimation)；[固定 commit](https://github.com/leggedrobotics/traversability_estimation/commit/14d24c059e1c43466aadf328280adf6394d78039) | [README](https://github.com/leggedrobotics/traversability_estimation/blob/master/README.md) | [BSD-3-Clause 风格](https://github.com/leggedrobotics/traversability_estimation/blob/master/LICENSE)；[#75](https://github.com/leggedrobotics/traversability_estimation/issues/75)、[#82](https://github.com/leggedrobotics/traversability_estimation/issues/82) |
| Wild Visual Navigation | [RSS 2023](https://www.roboticsproceedings.org/rss19/p054.html)；[2024/2025 扩展](https://arxiv.org/abs/2404.07110) | [仓库](https://github.com/leggedrobotics/wild_visual_navigation)；[固定 commit](https://github.com/leggedrobotics/wild_visual_navigation/commit/3d6d9d95d3b322956de4e9294e04639cfe30b3cd) | [README/quick start](https://github.com/leggedrobotics/wild_visual_navigation/blob/main/README.md)；[Docker](https://github.com/leggedrobotics/wild_visual_navigation/tree/main/docker) | [MIT](https://github.com/leggedrobotics/wild_visual_navigation/blob/main/LICENSE)；[#310](https://github.com/leggedrobotics/wild_visual_navigation/issues/310)、[#311](https://github.com/leggedrobotics/wild_visual_navigation/issues/311)、[#308](https://github.com/leggedrobotics/wild_visual_navigation/issues/308) |
| LeSTA | [IEEE RA-L 论文](https://ieeexplore.ieee.org/document/10468651) | [仓库](https://github.com/Ikhyeon-Cho/LeSTA)；[固定 commit](https://github.com/Ikhyeon-Cho/LeSTA/commit/c472db219744d4643954897d8b713e52d792d272) | [README、数据和 model zoo](https://github.com/Ikhyeon-Cho/LeSTA/blob/master/README.md)；[公开数据仓库](https://github.com/Ikhyeon-Cho/urban-traversability-dataset) | [Apache-2.0](https://github.com/Ikhyeon-Cho/LeSTA/blob/master/LICENSE)；[#15](https://github.com/Ikhyeon-Cho/LeSTA/issues/15)、[#9](https://github.com/Ikhyeon-Cho/LeSTA/issues/9) |

### 10.5 视觉—语言导航、VLA 与语义高层

| 候选 | 原始论文/项目页 | Canonical 仓库与固定快照 | 官方运行/资产证据 | 许可证/维护证据 |
|---|---|---|---|---|
| Habitat-Lab | [Habitat 1.0](https://arxiv.org/abs/1904.01201)、[2.0](https://arxiv.org/abs/2106.14405)、[3.0](https://arxiv.org/abs/2310.13724)；[官方文档](https://aihabitat.org/docs/habitat-lab/) | [仓库](https://github.com/facebookresearch/habitat-lab)；[固定 commit](https://github.com/facebookresearch/habitat-lab/commit/0fb6f43ffe806a8088a171b036336c093bcf604e) | [README 安装/测试](https://github.com/facebookresearch/habitat-lab/blob/main/README.md)；README 顶部含 v0.3.4 后不再由 Meta 主动维护的提示 | [MIT](https://github.com/facebookresearch/habitat-lab/blob/main/LICENSE)；[#2089](https://github.com/facebookresearch/habitat-lab/issues/2089)、[#2090](https://github.com/facebookresearch/habitat-lab/issues/2090)、[#2226](https://github.com/facebookresearch/habitat-lab/issues/2226) |
| VLN-CE | [Beyond the Nav-Graph](https://arxiv.org/abs/2004.02857)；[Waypoint Models](https://arxiv.org/abs/2110.02207)；[项目页](https://jacobkrantz.github.io/vlnce/) | [仓库](https://github.com/jacobkrantz/VLN-CE)；[固定 commit](https://github.com/jacobkrantz/VLN-CE/commit/729d141b2ee10628061ada74dd3a5b9f70faeba5) | [README: Python 3.6/Habitat 0.1.7/数据/评测](https://github.com/jacobkrantz/VLN-CE/blob/master/README.md) | [MIT](https://github.com/jacobkrantz/VLN-CE/blob/master/LICENSE)；场景/指令数据另有许可 |
| NaVILA | [论文](https://arxiv.org/abs/2412.04453)；[项目页](https://navila-bot.github.io/) | [仓库](https://github.com/AnjieCheng/NaVILA)；[固定 commit](https://github.com/AnjieCheng/NaVILA/commit/76b98f233dd0fff05dfcd69435eec6740febff9d) | [README/训练/评测](https://github.com/AnjieCheng/NaVILA/blob/main/README.md)；[Hugging Face 资产](https://huggingface.co/collections/a8cheng/navila-legged-robot-vision-language-action-model-for-naviga-67cfc82b83017babdcefd4ad)；[locomotion code](https://github.com/yang-zj1026/legged-loco) | [Apache-2.0](https://github.com/AnjieCheng/NaVILA/blob/main/LICENSE)；[#23](https://github.com/AnjieCheng/NaVILA/issues/23)、[#54](https://github.com/AnjieCheng/NaVILA/issues/54)、[#57](https://github.com/AnjieCheng/NaVILA/issues/57)、[#29](https://github.com/AnjieCheng/NaVILA/issues/29) |
| BehAV | [论文](https://arxiv.org/abs/2409.16484) | [仓库](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV)；[固定 commit](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV/commit/7ef5a48e175569a9bffa63e5725a1f378f3e55d7) | [README 与 planner 命令](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV/blob/main/README.md) | [Apache-2.0](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV/blob/main/LICENSE)；[#1 缺 orchestrator](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV/issues/1)、[#2 cost 逻辑](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV/issues/2) |
| WildOS | [论文](https://arxiv.org/abs/2602.19308)；[项目页](https://leggedrobotics.github.io/wildos/) | [仓库](https://github.com/nasa-jpl/nebula2-wildos)；[固定 commit](https://github.com/nasa-jpl/nebula2-wildos/commit/ffab44cb5f36e5508fbe29d3dc5bcd5fe69cb572) | [README/安装/checkpoints/launch](https://github.com/nasa-jpl/nebula2-wildos/blob/main/README.md)；[数据集](https://huggingface.co/datasets/leggedrobotics/wildos) | [Apache-2.0](https://github.com/nasa-jpl/nebula2-wildos/blob/main/LICENSE)；[#8 unknown layer](https://github.com/nasa-jpl/nebula2-wildos/issues/8) |
| Skill-Nav（参考，非开源候选） | [预印本](https://arxiv.org/abs/2506.21853)；[正式文章](https://doi.org/10.1007/s44336-025-00015-y) | **未找到公开 canonical 代码仓库** | 论文的 Code Availability 说明需向第一作者获取；无公开运行命令 | **未找到公开开源许可证**，因此仅作架构参考 |

### 10.6 关键接口结论的直接源码证据

| 结论 | 直接证据 |
|---|---|
| Lite3 厂商公开 ROS bridge 使用速度指令 | [Lite3_ROS README：`/cmd_vel` 与状态 topic](https://github.com/DeepRoboticsLab/Lite3_ROS#transfer) |
| Nav2 可以只计算路径，不要求使用原 controller | [ComputePathToPose action](https://api.nav2.org/actions/jazzy/computepathtopose.html) 和 [Planner Server 配置](https://docs.nav2.org/configuration/packages/configuring-planner-server.html) |
| Nav2 controller 可替换 | [Writing a New Nav2 Controller Plugin](https://docs.nav2.org/plugin_tutorials/docs/writing_new_nav2controller_plugin.html) |
| ViPlanner 的 planner 与 follower 分离 | [ROS integration README](https://github.com/leggedrobotics/viplanner/blob/main/ros/README.md) |
| ViPlanner follower 把 `nav_msgs/Path` 转为默认 `/cmd_vel` | [固定 commit 的 `pathFollower.cpp`](https://github.com/leggedrobotics/viplanner/blob/6fcf3c60f6fa3b28b3a11af054d6033825923789/ros/pathFollower/src/pathFollower.cpp) |
| WildOS 将语义/视觉高层与几何 Nav2 分层 | [README 的 Required External Components](https://github.com/nasa-jpl/nebula2-wildos#required-external-components) |
| NaVILA 使用高层语言动作 + 实时 locomotion 的两层结构 | [NaVILA README](https://github.com/AnjieCheng/NaVILA#-introduction) |

---

## 报告结尾：当前可陈述与不可陈述的结论

**可以陈述：**截至 2026-07-23，Nav2、ViPlanner、Quad-SDK、Elevation Mapping/WVN/LeSTA、NaVILA、WildOS 等有可检查的 canonical 开源实现；它们覆盖几何路径、局部视觉规划、四足全栈、可通行性和语义高层。Nav2 与 ViPlanner 提供最清晰的路径级拆分边界；Lite3 公开 ROS bridge 则只证明 `/cmd_vel` 可用，不能证明项目控制器支持 waypoint。

**不能陈述：**任何候选已经被本项目运行、复现、集成或验证；几何航点一定优于速度；Lite3 能安全执行某个路径；论文作者报告的性能已被独立验证；缺少许可证的仓库可被合法复制进项目；VLA/VLN 模型能够直接安全控制真机。

当前所有候选的项目证据状态：**`surveyed`**。
