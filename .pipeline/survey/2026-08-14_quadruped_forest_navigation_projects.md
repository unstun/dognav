---
origin: primary_source
reviewed: false
date: 2026-08-14
status: surveyed
---

# 2026-08-14 四足机器人森林自主导航项目定向调查

## 调查问题与边界

Dr Sun 询问：是否已有专门面向机器狗/四足机器人的森林场景项目可供
Lite3 自主导航参考。

- 检索范围：2020--2026 年，真实四足机器人在森林、林地、高草、灌木、
  落叶和倒木环境中的定位、可通行性、规划、运动控制与数据集。
- 证据优先级：论文原文、作者项目页、官方 GitHub 仓库和许可证文件。
- 本轮没有运行任何上游代码或数据，所有候选最高标记为 `surveyed`。
- “真实森林部署系统”“可回放森林数据”和“可直接导入 Isaac Sim 的物理
  森林场景”分开判断，不能互相替代。

## 核心结论

1. **有真正专门做四足机器人森林自主作业的系统：DigiForest 的 ANYmal
   森林清查系统。** 它覆盖 LiDAR--惯性状态估计、SLAM、局部地形图、
   森林可通行性、RMP 局部规划、任务规划和树木测量，并在芬兰、英国、
   瑞士的真实森林中持续部署。2025 年系统论文汇总了 2023--2024 年间
   5 次野外活动、16 次任务；早期论文报告 ANYmal D 在 Forest of Dean
   约 20 分钟完成 0.96 ha 调查并在线识别约 100 棵树。
2. **DigiForest 不是一个完整的一键开源仓库。** 但其局部规划核心
   `ori-drs/field_local_planner`、GPU 高程图
   `leggedrobotics/elevation_mapping_cupy` 已开源；视觉可通行性可直接参考
   `leggedrobotics/wild_visual_navigation`。任务管理、森林专用参数、完整
   VILENS/SLAM 部署和 ANYmal 低层控制仍不能从一个公共仓库完整复现。
3. **未找到“机器狗 + 完整森林 USD/Isaac 场景 + 传感器 + 物理 + 导航栈”
   的成熟开源项目。** 四足森林项目主要发布真实 rosbag/点云、算法代码或
   视频，而不是可直接导入 Isaac Sim 5.1 的森林物理世界。
4. 对本项目最有价值的路线不是立即替换 SCAN，而是：用 DigiForest 的真实
   失败模式设计森林测试场景；保留现有 Lite3 V12 + MID-360/D435i + SCAN
   闭环；把 RMP planner 和 Wild Visual Navigation 作为后续比较基线与
   可通行性增强模块。

## 候选速览

| 优先级 | 项目 | 四足/森林证据 | 公开程度 | 对 Lite3 的直接价值 |
|---|---|---|---|---|
| A1 | [DigiForest / Building Forest Inventories with Autonomous Legged Robots](https://arxiv.org/abs/2506.20315) | ANYmal C/D；芬兰、英国、瑞士真实森林；完整自主清查任务 | 完整系统没有单仓库；部分核心模块开源 | 最强系统架构、场景分层、失败模式和验收指标参考 |
| A2 | [Field Local Planner](https://github.com/ori-drs/field_local_planner) | DigiForest 论文所述 RMP 局部规划方法的公开实现 | ROS 1、GPL-3.0；RMP/FALCO/APF 插件齐全 | 可作为 SCAN 的森林局部规划比较基线；需 Foxy 移植或隔离桥接 |
| A3 | [Wild Visual Navigation](https://github.com/leggedrobotics/wild_visual_navigation) | ANYmal 真机；林径、高草和野外视觉可通行性；在线自监督 | MIT；核心 Python、ANYmal/Jackal ROS 1 包、Docker、模型与 rosbag 示例 | D435i 视觉语义/可通行性层的首选参考，不替代几何碰撞层 |
| A4 | [GrandTour Dataset](https://grand-tour.leggedrobotics.com/) | ANYmal D；包含 forest mission；LiDAR、相机、深度、IMU、关节/足端信息 | 数据 CC BY-SA-4.0；软件总体声明 MIT；ROS bag 需注册，ZARR 可直接获取 | 校准森林感知噪声、遮挡、振动和数据频率；不能直接当物理场景 |
| B1 | [APT-RL / KAIST HOUND](https://arxiv.org/abs/2607.13579) | HOUND 在倒木、树根、落叶和湿滑森林路径行进 0.34 km | 论文、项目页和视频公开；未找到官方代码/权重 | 代表森林 locomotion 能力上限；不是 A-to-B 规划器，无法直接移植 |
| B2 | [QuadSLAM Dataset](https://github.com/EN3D-Lab/Quadruped-SLAM-dataset) | Unitree Go2；高草、森林落叶、滑移/失衡/恢复；LiDAR+IMU+关节+接触 | rosbag 与真值公开；仓库未找到 LICENSE | 可做 Lite3/Go2 类机身振动与 SLAM 离线压力测试；不含导航闭环 |
| B3 | [ForestLPR](https://github.com/shenyanqing1105/ForestLPR-CVPR2025) | 使用森林 ANYmal 点云，专做林地 LiDAR 地点识别 | 训练/评测代码公开；仓库未找到 LICENSE | 可参考重复树干环境的回环/重定位，不负责局部避障或运动 |
| B4 | [ArtPlanner](https://github.com/leggedrobotics/art_planner) | ANYmal 野外粗糙地形规划，但不是森林专用项目 | BSD-3-Clause；ROS Noetic、OMPL、GridMap、PyTorch | 适合作为 2.5D 本体可达性/运动代价规划基线，ANYmal 权重不可直接套 Lite3 |
| C | [SPOT's First Steps](https://doi.org/10.3390/f14112170) | Boston Dynamics Spot 的森林清查初步试验 | 论文公开；未找到配套导航代码 | 证明 Spot 可用于林业采集，但不足以作为自主规划实现基座 |

## 最值得拆解的系统：DigiForest

### 系统结构

DigiForest 不是端到端神经网络，而是清晰的分层系统：

1. **状态估计与地图**：LiDAR--inertial odometry、pose-graph LiDAR SLAM、
   稠密局部子图，以及供导航使用的 2.5D 局部地形图。系统论文报告局部图
   尺寸为 4 m x 4 m、分辨率为 4 cm。
2. **任务层**：操作员指定调查区域，boustrophedon/lawn-mower pattern 生成
   粗航点；mission planner 调度航点，并在局部规划器报告不可达时更换目标。
3. **局部规划层**：森林专用几何可通行性分数处理树枝、细枝和未知区域；
   再用 Riemannian Motion Policies 组合 SDF 碰撞场和 GDF 目标引导场，输出
   `(vx, vy, yaw_rate)`。
4. **运动层**：ANYmal 的学习型 locomotion controller 执行三自由度速度命令。
   论文明确说森林部署没有为低层策略专门重新训练。

这条接口与本项目的“规划器 -> 速度命令 -> V12 locomotion policy”边界高度
相似，因此 DigiForest 更适合作为森林主参考，而 ViPlanner 更适合作为学习型
局部规划对照。

### 真机结果不能被简化成“全自主成功”

系统确实完成了大尺度真实森林任务，但论文也保留了安全员干预：

- 早期 7 次任务中只有一条任务完全无干预；其他任务常因局部极小、死胡同、
  状态估计漂移或不可达航点需要短时人工“推一把”。
- 湿地/bog 没有被机载感知识别，机器人会下陷并卡住。
- 松散树枝可能夹住腿；高密灌木会造成跌倒或让局部规划无法可靠判断。
- 论文把局部规划器和规划--运动耦合列为主要待改进模块。

因此我们后续仿真不能只摆规则树干；至少要覆盖倒木、细枝、密灌木、死胡同、
遮挡和未知区域。泥地/下陷在刚体 PhysX 中只能做近似风险测试，不能声称复现
真实软土。

## 已核验的开源仓库固定版本

核验时间：2026-08-14。`pushed_at` 只反映仓库活动，不等于本项目已运行。

| 仓库 | 分支与固定 commit | 许可证 | 依赖/原作者入口 | 项目状态 |
|---|---|---|---|---|
| `ori-drs/field_local_planner` | `master` @ `f1f8f0fd5fcb38527026747eea469ff19cdd853e`；2025-03-03 推送 | GPL-3.0 | ROS 1；`grid_map_filters_drs`、`teleop_twist_joy`；`roslaunch field_local_planner_ros <planner>.launch` | surveyed |
| `leggedrobotics/wild_visual_navigation` | `main` @ `3d6d9d95d3b322956de4e9294e04639cfe30b3cd`；2026-05-27 推送 | MIT | ROS 1 Noetic、CUDA GPU、Python、STEGO；Docker；`python3 quick_start.py` 或 `roslaunch wild_visual_navigation_ros wild_visual_navigation.launch` | surveyed |
| `leggedrobotics/elevation_mapping_cupy` | `main` @ `20a8a26b67a995b43eb44c23568854d1fed82a52`；2026-07-25 推送 | MIT | GPU/CuPy、GridMap、catkin/Docker；仓库同时存在 ROS 1/ROS 2 代际，采用前必须固定目标分支/标签 | surveyed |
| `leggedrobotics/art_planner` | `main` @ `2f3fde68b8ac55f6f91083acc4d09df2b10f3c1f`；2023-08-09 推送 | BSD-3-Clause | ROS Noetic、OMPL、GridMap、修改版 ODE、可选 PyTorch 1.13；`roslaunch art_planner_ros art_planner.launch` | surveyed |
| `leggedrobotics/grand_tour_box` | `main` @ `7c7b7884e06a2082ac11f7b8a2ef3b7d25de5062`；2026-05-05 推送 | MIT | 大型采集/处理栈；普通使用优先 `kleinkram`、ROS bag 或 ZARR 示例 | surveyed |
| `EN3D-Lab/Quadruped-SLAM-dataset` | `main` @ `0c58b27d4645ee91cc23615b34866e473b00d69f`；2026-02-14 推送 | **未找到许可证文件** | ROS 1 bag、Go2 消息、LiDAR/IMU/关节/足端力；`evo_ape` 评测示例 | surveyed; license blocked |
| `shenyanqing1105/ForestLPR-CVPR2025` | `main` @ `fe402ea6221a61183af5501f19c390179c09f55d`；2025-07-03 推送 | **未找到许可证文件** | CUDA 11.8、Python 3.9.4、PyTorch 2.0.1、Conda；需另取处理后的 ANYmal/Wild-Places 数据 | surveyed; license blocked |

## 对当前 SCAN/Lite3 仿真的具体建议

### 主线：DigiForest-inspired Forest V4，不换规划器

在当前已通过自动门、仍等待人工验收的 SCAN + Lite3 V12 + MID-360/D435i
闭环上新增一组场景，而不是覆盖既有 V1/V2/V3 证据：

| 场景 | 来自真实部署的风险 | 仿真可验证内容 |
|---|---|---|
| F1 稀疏针叶林 | 清晰树干、低灌木少 | 基本点云、树间绕行、长路径跟踪 |
| F2 混交坡地 | 坡度、落叶、散落枝条 | 足地接触、倒木绕行、机身/腿碰撞 |
| F3 密灌木与细树 | 遮挡、未知区、树后目标 | SCAN 空间碰撞、保守未知区和重新选路 |
| F4 林间死胡同 | 局部极小、航点不可达 | 停滞检测、回退和全局/局部重规划接口 |
| F5 松枝/低枝 | 腿被卡、机身上方碰撞 | 双圆柱/3D 机身碰撞模型是否漏检 |
| F6 湿地近似 | 下陷、低摩擦、感知不可见风险 | 仅做摩擦/支撑退化压力测试；不声称软土真实性 |

### 第二阶段比较项

1. **RMP baseline**：固定 `field_local_planner` 的 RMP/FALCO 算法语义，先离线
   对同一地形图比较路径/速度，再决定是否值得移植到 Foxy。GPL-3.0 代码要与
   Apache-2.0 SCAN 主线隔离。
2. **WVN traversability layer**：先对 GrandTour/WVN rosbag 做离线推理，证明
   能区分硬树干、道路、高草和灌木，再考虑把 D435i 输出融合到代价图。它不是
   碰撞检查器，不能单独决定 Lite3 是否可穿越。
3. **真实数据回归**：GrandTour forest sequence 和 QuadSLAM 的高草/落叶序列
   用于感知与定位回放，不用于声称 Isaac 场景真实。

## 本地保存的原文

- `docs/research/papers/2506.20315-DigiForest-ANYmal-Forest-Inventory.pdf`
- `docs/research/papers/2404.07110-Wild-Visual-Navigation.pdf`
- `docs/research/papers/2602.18164-GrandTour-Legged-Robotics-Dataset.pdf`
- `docs/research/papers/2607.13579-APT-RL-HOUND-Wild-Locomotion.pdf`
- `docs/research/papers/2403.14326-Forest-LiDAR-Place-Recognition.pdf`

## 未解决项

- 未找到 DigiForest 完整任务规划、森林参数、VILENS-SLAM 部署和 ANYmal
  locomotion 的统一公共仓库。
- 未找到上述四足森林项目发布可直接导入 Isaac Sim 5.1 的带碰撞 USD/场景包。
- APT-RL 未找到官方代码、训练环境或权重发布。
- QuadSLAM 和 ForestLPR 仓库缺少明确许可证，未解决前只能做阅读和内部评估，
  不应复制代码进入主线。
- GrandTour 的 ROS bag 需要注册；ZARR 无需注册，但是否含满足本项目需求的
  完整 forest mission 字段需下载后再核验。
