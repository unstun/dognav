---
origin: primary_source
reviewed: false
date: 2026-07-23
status: surveyed
---

# 2026-07-23 四足机器人导航开源仓库补充调查

## 调查边界

- 本轮重新联网广搜并核验 GitHub canonical 仓库、论文原文、许可证、分支、固定 commit、README、代码目录和公开运行说明。
- 共筛查 35 个候选；对 11 个高潜候选做了更深的仓库审计。
- 本轮没有运行上游代码。因此所有结论最高只能标为 `surveyed`，不能标为 `reproduced`、`integrated` 或 `validated`。
- 本报告补充并纠正
  [`docs/research/2026-07-23-lite3-navigation-open-source-survey.md`](../../docs/research/2026-07-23-lite3-navigation-open-source-survey.md)
  中对最新四足专用仓库覆盖不足的问题。

## 结论

### 没有一个仓库同时满足“最新、成熟、四足专用、可直接装到 Lite3”

截至 2026-07-23，公开代码中没有发现已经针对 Lite3 打通感知、定位、
建图、规划、避障和运动控制的完整导航仓库。Lite3 官方
[`Lite3_ROS`](https://github.com/DeepRoboticsLab/Lite3_ROS)
只是 ROS 2 与运动主机之间的 UDP 桥：发布腿里程计、IMU 和关节状态，订阅
`/cmd_vel`。它没有 SLAM、地图、全局规划器或局部避障器。

因此，“哪个最靠谱”必须按用途回答：

| 用途 | 当前建议 | 结论 |
|---|---|---|
| Lite3 第一条可审计导航闭环 | [Nav2](https://github.com/ros-navigation/navigation2) + Lite3 `/cmd_vel` 桥 | 工程底座最可靠；不是四足专用先进算法 |
| 最新四足局部规划算法 | [SCAN-Planner](https://github.com/wuyi2121/SCAN-Planner) | 2026-07 刚释出主算法；新，但还不成熟 |
| 四足规划—足步—控制纵向全栈 | [Quad-SDK `devel_ros2`](https://github.com/robomechanics/quad-sdk/tree/devel_ros2) | 老项目的新活跃分支；功能完整，但 Lite3 适配代价大 |
| 最接近“低成本四足完整导航参考实现” | [quad-stack](https://github.com/dyumanaditya/quad-stack) | 论文和代码边界完整；仓库工程质量仍不足以称即装即用 |
| 最新户外语义探索研究栈 | [WildOS](https://github.com/nasa-jpl/nebula2-wildos) | 代码、权重和图规划器已公开；任务重、算力重、Spot 特化 |
| 最新端到端四足 RL 导航 | [SEA-Nav](https://github.com/11chens/SEA-Nav-Code) | 值得跟踪；当前不应作为首个基线 |

如果必须给本项目一个执行选择，建议：

1. 用 Nav2 建立第一条 Lite3 几何导航基线；
2. 把 SCAN-Planner 作为第一项“最新四足局部规划器”对比实验；
3. 把 Quad-SDK 和 quad-stack 分别作为纵向全身规划、完整导航系统的参考，
   不直接把其中任一仓库整体移植进 Lite3；
4. WildOS、SEA-Nav 留作后续前沿方向。

这比单独选择 Quad-SDK 更符合 `machine-dog-nav` 当前“先打通导航到既有运动控制”
的项目边界。

## 评价口径

本轮没有按 star 数或 README 演示排序，而是检查：

1. canonical URL 和明确许可证；
2. 默认分支与真正活跃分支是否一致；
3. 固定 commit 和最近实质代码更新时间；
4. 是否有真实代码，而不是项目页、占位目录或“coming soon”；
5. 是否提供安装、模型、配置和运行命令；
6. 仿真、实机、机器人、传感器和计算平台证据；
7. 输出是路径、航点、速度还是关节级命令；
8. 对 Lite3 `/cmd_vel` 运动控制边界的适配成本；
9. 是否有 release、CI、测试和可重复依赖；
10. 论文中的实机结果与仓库当前可运行边界是否一致。

“作者报告实机成功”不等于本项目已复现；“分支最近更新”也不等于代码成熟。

## 深度核验结果

### 1. Nav2：最可靠的工程底座

- 仓库：[ros-navigation/navigation2](https://github.com/ros-navigation/navigation2)
- 核验 commit：
  [`db906947171abe170c25181347be9bc7bcbc1a75`](https://github.com/ros-navigation/navigation2/commit/db906947171abe170c25181347be9bc7bcbc1a75),
  2026-07-22
- 最近 release：`1.3.12`，2026-04-29
- 许可证：仓库按 package 混合使用 LGPL-2.1-or-later、Apache-2.0 和
  BSD-3-Clause；根目录声明未特别标注的文件采用 Apache-2.0。
- 证据：持续维护、多 ROS 2 发行版、CI、系统测试、插件化 planner/controller、
  collision monitor、velocity smoother、waypoint follower。
- Lite3 接口：Nav2 controller 通常输出 `Twist`/`TwistStamped`，与 Lite3 官方
  `/cmd_vel` 桥接方向一致。
- 限制：Nav2 默认把机器人抽象为平面移动底盘，不会自动解决足端可行性、台阶、
  坡面、机身碰撞或四足动态稳定。

结论：它不是最新四足论文算法，但仍是本项目最可靠的第一工程基线。

### 2. Quad-SDK：不是新项目，但活跃分支不是四年前

- 仓库：[robomechanics/quad-sdk](https://github.com/robomechanics/quad-sdk)
- 创建时间：2020-08-30；框架论文发表于 2022。
- 默认 `main`：
  [`50b58ce8f248...`](https://github.com/robomechanics/quad-sdk/commit/50b58ce8f248),
  最近 commit 为 2024-04-25。
- 当前活跃分支：
  [`devel_ros2`](https://github.com/robomechanics/quad-sdk/tree/devel_ros2)，固定
  [`b989ef9f98c9f7dfee465fa63350a2e5150c537f`](https://github.com/robomechanics/quad-sdk/commit/b989ef9f98c9f7dfee465fa63350a2e5150c537f),
  2026-06-09。
- 分支事实：`devel_ros2` 与 `main` 已明显分叉；GitHub compare 显示
  ahead 729 commits、behind 147 commits、约 300 个变更文件。GitHub API 在
  2026-01-01 之后列出 131 个该分支 commit。
- 2026 年实质更新包括 ROS 2 Jazzy、Gazebo Harmonic、MuJoCo、多机器人、
  Pinocchio、NMPC、Unitree A2、硬件部署和回归测试。
- 许可证：MIT。
- 支持平台：Go1、Go2、Go2-W、A1、A2、B2、Spot、Vision60 和研究平台；
  不含 Lite3。
- 输入/输出边界：可以接受 twist 输入，但内部纵向贯穿全局 body planner、
  NMPC local planner、足步、估计和 robot driver。
- 主要依赖和成本：ROS 2 Jazzy / Ubuntu 24.04、CasADi、IPOPT、机器人模型与
  硬件接口适配；分支 README 明确称其为频繁变化的 research code。

结论：用户对“Quad-SDK 是四年前的”质疑是正确的——它不是 2026 年的新项目。
准确说法是“老项目 + 2026 年高度活跃但尚未合回默认分支的 ROS 2 重构线”。
它可作为四足纵向全栈研究对象，但不是 Lite3 第一条导航闭环的低成本选择。

### 3. quad-stack：最接近完整低成本四足导航参考，但工程仍粗糙

- 仓库：[dyumanaditya/quad-stack](https://github.com/dyumanaditya/quad-stack)
- 论文：
  [Robust Localization, Mapping, and Navigation for Quadruped Robots](https://arxiv.org/abs/2505.02272)
- 核验 commit：
  [`bb528fd6d799bcd94df54942ecb447c441b13380`](https://github.com/dyumanaditya/quad-stack/commit/bb528fd6d799bcd94df54942ecb447c441b13380),
  2025-10-26
- 许可证：BSD-3-Clause。
- ROS：ROS 2 Humble；Gazebo Classic。
- 机器人：MAB Silver/Honey Badger、Unitree A1/Go1/Go2。
- 能力：神经运动控制、接触辅助运动学、视觉惯性里程计、速度约束 SLAM、
  Nav2、已知地图导航和 frontier exploration。
- 论文证据：作者报告在两种真实四足平台上验证定位、建图和自主导航。
- 代码证据：434 个 tracked blob，包含 Go2 模型、策略、真实 Go2 relay、
  odometry/SLAM/navigation launch、Nav2 参数和 tests。
- 风险：
  - 无 release、无 CI workflow；
  - `setup.sh` 直接安装和升级系统/Python 包，并克隆未固定 commit 的依赖；
  - 有重复 import、硬编码路径、Gazebo Classic 和 `use_sim_time` 等工程痕迹；
  - README 的“real robot”启动边界有一部分实际是 rosbag 回放路径。

结论：比单一 planner 更适合研究“完整四足导航系统如何接起来”，但还不能称为
Lite3 即装即用仓库。作为第二个 upstream reproduction 对象比作为直接产品依赖更合适。

### 4. SCAN-Planner：目前最新、最值得看的四足局部规划器

- 仓库：[wuyi2121/SCAN-Planner](https://github.com/wuyi2121/SCAN-Planner)
- 论文：
  [SCAN-Planner: Spatial Collision-Aware Local Planning for Route-Guided Long-Range Quadruped Navigation](https://arxiv.org/abs/2606.19555)
- 默认 `main` 固定：
  [`529f0ba43b7e79e6fff85a5777c786237f0f8f33`](https://github.com/wuyi2121/SCAN-Planner/commit/529f0ba43b7e79e6fff85a5777c786237f0f8f33),
  2026-07-16
- 许可证：Apache-2.0。
- 主分支：Ubuntu 20.04、ROS Noetic；2026-07-09 公开主算法。
- 传感器：点云 LiDAR（示例 MID360）或深度相机（示例 RealSense D435）。
- 机器人参数：默认面向 Unitree Go2。
- 模式：RViz 目标、跨楼层 keypoint、参考路径跟踪 + 局部避障。
- ROS 2：
  [`ros2-community`](https://github.com/wuyi2121/SCAN-Planner/tree/ros2-community)
  固定
  [`d0b921c9b05a6d291d144d60882b2e0e88d2c0e0`](https://github.com/wuyi2121/SCAN-Planner/commit/d0b921c9b05a6d291d144d60882b2e0e88d2c0e0),
  2026-07-13。该分支 README 明确声明是社区自移植，不代表原作者官方发布；
  分支未保护，且与 `main` 没有共同 ancestor。
- 运行边界：提供仿真和 planner launch；真机仍需外部 LIO、相机和 Unitree driver。
- 成熟度风险：无 release、无 CI workflow、算法公开不足两周。

结论：如果问题是“最新四足导航算法代码是哪一个最值得先看”，本轮首选
SCAN-Planner；如果问题是“哪个最稳”，它还不能超过 Nav2。

### 5. WildOS：2026 年最完整的户外语义探索代码之一

- 仓库：[nasa-jpl/nebula2-wildos](https://github.com/nasa-jpl/nebula2-wildos)
- 论文：
  [WildOS: Open-Vocabulary Object Search in the Wild](https://arxiv.org/abs/2602.19308)
- 核验 commit：
  [`ffab44cb5f36e5508fbe29d3dc5bcd5fe69cb572`](https://github.com/nasa-jpl/nebula2-wildos/commit/ffab44cb5f36e5508fbe29d3dc5bcd5fe69cb572),
  2026-07-13
- 许可证：Apache-2.0。
- ROS：ROS 2 Jazzy。
- 代码：视觉 frontier/traversability/object similarity、训练代码、预训练 head、
  3D 目标三角化、graph mapper、graph planner 和消息定义已在仓库中。
- 外部组件：Elevation Mapping CuPy、DLIO、Nav2。
- 平台：论文和文档面向 Spot；训练用 RTX 4090，部署用 Jetson AGX Orin。
- 任务：无先验地图的长距离开放词汇目标搜索，不是普通 point-goal 导航基线。

结论：前一次调查把 graph construction 看成“未来发布”已经过时；2026-07-13
commit 已加入 graphnav mapper。它是值得保留的最新高级研究候选，但不适合作为
Lite3 第一条最小闭环。

### 6. SEA-Nav：很新、代码有实机分支，但当前不够可靠

- 仓库：[11chens/SEA-Nav-Code](https://github.com/11chens/SEA-Nav-Code)
- 论文：
  [SEA-Nav: Efficient Policy Learning for Safe and Agile Quadruped Navigation in Cluttered Environments](https://arxiv.org/abs/2603.09460)
- 默认 `main`：
  [`fbce672c22d432e0ba8c9ef1b1e822f8fbd3ec96`](https://github.com/11chens/SEA-Nav-Code/commit/fbce672c22d432e0ba8c9ef1b1e822f8fbd3ec96),
  2026-03-24。
- 默认分支现状：训练和 play 命令存在；`deployment/README.md` 只有
  `Coming soon.`。
- 未合并部署分支：
  [`liuhy25/sim2real-deployment`](https://github.com/11chens/SEA-Nav-Code/tree/liuhy25/sim2real-deployment)
  固定
  [`8abff95834ade1310e2e7cde33489040924b46a0`](https://github.com/11chens/SEA-Nav-Code/commit/8abff95834ade1310e2e7cde33489040924b46a0),
  2026-07-18；相对 `main` ahead 3 commits，含 18 个 deployment 文件。
- 部署边界：Go2 + RPLIDAR A2M12 + BreezySLAM；`/rays` 和 `/pose` 输入；
  高层策略输出 `vx, vy, vyaw`，低层策略直接生成 12 关节命令并向 Go2
  `rt/lowcmd` 写入。
- 风险：
  - 根仓库无明确许可证；
  - 部署只在未保护、未合并分支；
  - 需要外部 `quad_deploy` 特定分支、模型和多个依赖仓库；
  - 文档中的 Sim2Sim 验证和部署说明不能替代本项目独立实机证据；
  - 直接关节级控制的安全风险远高于 `/cmd_vel` 适配。

结论：这是本轮重要补充，不能再说 SEA-Nav “没有部署代码”；但也不能因为分支
最新就把它称为最可靠。当前适合监测和离线审计，不适合首先驱动 Lite3。

### 7. DDDMR Navigation：活跃的 3D 导航工程栈

- 仓库：[dfl-rlab/dddmr_navigation](https://github.com/dfl-rlab/dddmr_navigation)
- 核验 commit：
  [`1d0367376380205a6a18c0ad7c7c16c9338c96bc`](https://github.com/dfl-rlab/dddmr_navigation/commit/1d0367376380205a6a18c0ad7c7c16c9338c96bc),
  2026-07-18
- 许可证：BSD-3-Clause。
- 能力：3D mapping、3D localization、global/local planner、3D perception 和
  Go2 Gazebo simulator。
- 优点：面向坡道、多楼层和立体结构，维护活跃，代码量完整。
- 限制：它是通用 3D mobile robot stack；公开 Go2 证据以模拟器为主，
  没有看到与 quad-stack 同等级的四足实机论文和 Lite3 适配证据。

结论：值得作为 Nav2 之外的 3D 导航基线候选，但不是已证实的 Lite3 全栈。

### 8. TRG-planner：算法可靠性有论文支撑，许可证不是标准开源

- canonical 仓库当前为
  [wasahaiah/TRG-planner](https://github.com/wasahaiah/TRG-planner)；
  README 内旧组织 URL 已失效或迁移。
- 论文：
  [TRG-planner: Traversal Risk Graph-Based Path Planning](https://arxiv.org/abs/2501.01806)
- 核验 commit：
  [`fc6f1e47d1e642eedcf87892f341794dc91890ec`](https://github.com/wasahaiah/TRG-planner/commit/fc6f1e47d1e642eedcf87892f341794dc91890ec),
  2025-03-14
- ROS 1 Noetic 和 ROS 2 Humble pipeline，C++/Python 接口。
- 许可证：`Apache-2.0 with Commons Clause`，包含非标准商业限制，严格来说
  不是 OSI 定义的开源许可证。
- 作者报告该 planner 用于 IEEE Quadruped Robot Challenge 获奖系统。

结论：可作为算法对照和 source-available 研究材料；在许可证审查前不应直接纳入
本项目开源代码。

### 9. ViPlanner：仍是成熟的学习型局部路径候选，但不再是“最新”

- 仓库：[leggedrobotics/viplanner](https://github.com/leggedrobotics/viplanner)
- 核验 commit：
  [`6fcf3c60f6fa3b28b3a11af054d6033825923789`](https://github.com/leggedrobotics/viplanner/commit/6fcf3c60f6fa3b28b3a11af054d6033825923789),
  2025-02-12
- 许可证：BSD-3-Clause。
- 优点：ANYmal 实机、Isaac Sim 训练、ROS Noetic inference、路径与 follower
  边界清楚。
- 限制：ROS 1、CUDA/mmcv/旧 Isaac 环境；当前维护活动明显低于 WildOS、
  SCAN-Planner 和 Quad-SDK `devel_ros2`。

结论：保留为成熟学习型局部规划对照，不再把它表述为最新候选。

### 10. EasyNav：非常活跃的现代 ROS 2 通用导航框架

- 仓库：[EasyNavigation/EasyNavigation](https://github.com/EasyNavigation/EasyNavigation)
- 核验 rolling commit：
  [`2063ebd95ca0e5f1ab192486f551385f25323beb`](https://github.com/EasyNavigation/EasyNavigation/commit/2063ebd95ca0e5f1ab192486f551385f25323beb),
  2026-07-23
- 许可证：Apache-2.0；有 `0.3.x` tags。
- CI：rolling、Kilted、Jazzy、Humble。
- 优点：representation-agnostic，可用 2D costmap、grid map、Octomap、
  point cloud 或混合表示，插件化且比 Nav2 更轻。
- 限制：项目创建于 2025，社区和实机积累远低于 Nav2；官方 playground
  主要是 Kobuki 和 Summit XL，不是四足机器人。

结论：值得监测并作为框架设计参考；当前不能替代 Nav2 作为最稳基线。

### 11. Lite3 官方和社区仓库

#### Lite3_ROS

- 仓库：[DeepRoboticsLab/Lite3_ROS](https://github.com/DeepRoboticsLab/Lite3_ROS)
- 固定：
  [`e4ab5dc1c7f3ff46274162a1ef302253936578aa`](https://github.com/DeepRoboticsLab/Lite3_ROS/commit/e4ab5dc1c7f3ff46274162a1ef302253936578aa),
  2026-02-05
- 许可证：MIT；默认分支 `ros2-foxy`。
- 输出：`/leg_odom`、`/leg_odom2`、`/imu/data`、`/joint_states`。
- 输入：`/cmd_vel` (`geometry_msgs/Twist`)。
- 定位：它是必要的机器人接口候选，不是导航算法仓库。

#### Lite3_SLAM_NAV

- 仓库：
  [Bao-Trinh-Quoc/Lite3_SLAM_NAV](https://github.com/Bao-Trinh-Quoc/Lite3_SLAM_NAV)
- 2026-06 创建，GitHub repo size 为 0，只有 87-byte README，无明确许可证、
  无导航源代码。

结论：目前没有可信的 Lite3 社区完整导航栈可以直接采用。

## 广搜候选清单

下表中的“筛查”只表示检查过仓库定位、更新时间、许可证和主要代码边界；
未进入深度核验的仓库不应被解读为质量差，只表示与当前 Lite3 第一阶段的匹配度较低。

| 类别 | 候选 | 筛查结论 |
|---|---|---|
| 工程底座 | [Nav2](https://github.com/ros-navigation/navigation2) | 深度核验；首选基线 |
| 工程底座 | [EasyNav](https://github.com/EasyNavigation/EasyNavigation) | 深度核验；活跃但年轻 |
| 四足纵向全栈 | [Quad-SDK](https://github.com/robomechanics/quad-sdk/tree/devel_ros2) | 深度核验；活跃分支，不是新项目 |
| 四足完整导航 | [quad-stack](https://github.com/dyumanaditya/quad-stack) | 深度核验；完整但工程粗糙 |
| 四足局部规划 | [SCAN-Planner](https://github.com/wuyi2121/SCAN-Planner) | 深度核验；最新重点候选 |
| 户外语义探索 | [WildOS](https://github.com/nasa-jpl/nebula2-wildos) | 深度核验；高级重点候选 |
| 四足 RL 导航 | [SEA-Nav](https://github.com/11chens/SEA-Nav-Code) | 深度核验；部署分支存在但暂缓 |
| 3D 导航栈 | [DDDMR Navigation](https://github.com/dfl-rlab/dddmr_navigation) | 深度核验；Go2 主要为模拟证据 |
| 风险图规划 | [TRG-planner](https://github.com/wasahaiah/TRG-planner) | 深度核验；Commons Clause |
| 学习型局部规划 | [ViPlanner](https://github.com/leggedrobotics/viplanner) | 深度核验；成熟但不新 |
| Lite3 接口 | [Lite3_ROS](https://github.com/DeepRoboticsLab/Lite3_ROS) | 深度核验；只做接口 |
| 动态避障 RL | [NavRL](https://github.com/Zhefan-Xu/NavRL) | Go2 ROS 2/Isaac Sim 示例；原论文为 UAV |
| 视觉 teach-and-repeat | [GuideNav](https://github.com/guidedogrobot-navigation/GuideNav) | 2026、MIT、四足实机；任务不是任意 point-goal |
| 四足 Gazebo/Nav2 | [RCI quadruped navigation](https://github.com/RCILab/RCI_quadruped_robot_navigation) | ROS 2 Humble，Go2/Go2W/B2；主要是 Sim2Sim |
| 产品化 ROS 2 栈 | [BotBrain](https://github.com/botbotrobotics/BotBrain) | Go2/Go2-W + RTAB-Map + Nav2；工程范围大、研究证据弱 |
| Go2 Nav2 | [unitree_go2_nav](https://github.com/Sayantani-Bhattacharya/unitree_go2_nav) | 实机说明完整；无明确许可证、已知 URDF 问题 |
| Go2 Nav2 | [unitree-go2-slam-nav2](https://github.com/h-naderi/unitree-go2-slam-nav2) | 小型集成仓库；无明确许可证 |
| Go2 工具箱 | [go2_ros2_toolbox](https://github.com/andy-zhuo-02/go2_ros2_toolbox) | MIT；更偏模拟/接口工具 |
| Go2 基础栈 | [Unitree-Go2-Robot/go2_robot](https://github.com/Unitree-Go2-Robot/go2_robot) | Apache-2.0；更偏 ROS 2 驱动和基础包 |
| Go2 基础栈 | [go2_ros2_sdk](https://github.com/abizovnuralem/go2_ros2_sdk) | BSD-2-Clause、维护活跃；驱动，不是完整导航 |
| Go2 仿真 | [isaac-go2-ros2](https://github.com/Zhefan-Xu/isaac-go2-ros2) | 高使用度；无明确许可证、不是完整导航 |
| Go2 Nav2 | [go2-nav2-wifi](https://github.com/dancher00/go2-nav2-wifi) | 2026、MIT；很新、证据少 |
| Go2 Nav2 | [ASIL go2-autonomous-navigation](https://github.com/asil-lab/go2-autonomous-navigation) | GPL-3.0；小型工程集成 |
| Go2-W agent | [unitree_go2w_agent_sdk](https://github.com/grasp-lyrl/unitree_go2w_agent_sdk) | 无明确许可证；偏 agent/SDK |
| 视觉运动规划 | [TOP-Nav](https://github.com/TOP-Nav-Legged/TOP-Nav-Legged) | 代码仓库很小、无明确许可证 |
| VLM 户外导航 | [BehAV](https://github.com/GAMMA-UMD-Outdoor-Navigation/BehAV) | Apache-2.0；四足实机，高层行为约束研究 |
| VLA/VLN | [NaVILA](https://github.com/AnjieCheng/NaVILA) | Apache-2.0；高层指令/航点，不是底层导航栈 |
| 自监督可通行性 | [Wild Visual Navigation](https://github.com/leggedrobotics/wild_visual_navigation) | MIT、持续维护；输出风险/可通行性，不是完整栈 |
| 多机器人 VLM | [Triple-Zero](https://github.com/triple-zeropp/Triple-zero-robot-agent) | MIT；G1 + Go2，多机器人任务，不是单机基线 |
| 轨迹优化 | [QTOS](https://github.com/Alexyskoutnev/Quadruped-Trajectory-Optimization-Stack) | MIT、2023；完整概念但已停止活跃 |
| 3D 路径规划 | [FAR Planner](https://github.com/MichaelFYang/far_planner) | 许可证缺失和外部仿真依赖仍未解除 |
| 探索 | [TARE](https://github.com/caochao39/tare_planner) | 探索任务，不是第一条 point-goal 闭环 |
| Lite3 社区 | [Lite3_SLAM_NAV](https://github.com/Bao-Trinh-Quoc/Lite3_SLAM_NAV) | 空仓库，排除 |
| 四足社交导航 | LiSA-Nav | 论文线索；本轮未确认可用 canonical 代码 |
| 地下矿山 Spot 导航 | [Efficient Autonomous Navigation on Edge Hardware](https://arxiv.org/abs/2603.04470) | 2026 实机论文；未发现论文绑定的公开代码 |

## 对原调查的纠偏

原调查“内容不少但候选面不够宽”，主要缺少：

1. 2026-06/07 新发布的 SCAN-Planner；
2. SEA-Nav 未合并但实际存在的 sim-to-real deployment 分支；
3. quad-stack 这一套低成本四足定位、建图、导航论文代码；
4. DDDMR、EasyNav、BotBrain 等 2025–2026 ROS 2 工程栈；
5. GuideNav、Triple-Zero、地下矿山 Spot 导航等新的任务形态；
6. Quad-SDK 默认 `main` 与 `devel_ros2` 的分支事实；
7. WildOS 在 2026-07-13 已补齐 graph mapper 的状态变化；
8. TRG-planner 的 canonical 仓库迁移和 Commons Clause 许可证问题。

因此，旧报告中的“Nav2 最可靠工程底座”结论仍成立，但“最新候选”和
“四足专用候选”的覆盖与排序需要以本报告为准。

## 推荐的下一步复现顺序

这不是本轮已经执行的结果，只是基于源码审计得出的下一阶段建议：

1. **Nav2 最小闭环**：固定 ROS 2 发行版和 Nav2 release，在仿真中验证
   goal → path → bounded `/cmd_vel`，保存命令、日志和 bag。
2. **SCAN-Planner 原生仿真**：先按主分支 ROS Noetic 原命令复现，不先使用
   非官方 ROS 2 port；记录路径/局部控制输出。
3. **quad-stack smoke**：在容器或隔离环境中修正未固定依赖，验证 Go2 simulation
   的 odometry → SLAM → Nav2 闭环。
4. **Quad-SDK `devel_ros2`**：仅当研究目标明确包含 body trajectory、足步和
   NMPC 时，再做 Gazebo/MuJoCo 原生复现。
5. **Lite3 集成**：在以上 upstream 原生结果稳定后，单独定义
   `/cmd_vel`、状态估计、frame、watchdog、急停和 locomotion commit 契约。

任何实机控制、SEA-Nav 关节级部署或长训练都必须另行获得 Dr Sun 明确授权。

## 当前状态

- `surveyed`：本报告所有仓库。
- `reproduced`：无。
- `integrated`：无。
- `validated`：无。
