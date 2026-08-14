---
origin: primary_source
reviewed: false
date: 2026-08-14
status: surveyed
---

# 2026-08-14 森林地形与场景资产上游调查

## 范围修正

Dr Sun 明确本轮重点是**森林地形和场景本身**，不是更换规划算法。筛选标准
因此改为：

1. 是否包含真实三维地面、树木、灌木、草、岩石或倒木资产；
2. 是否能形成具有碰撞的物理场景，而不只是点云或渲染背景；
3. 是否支持固定随机种子、密度、树径、坡度、林道和障碍布局；
4. 迁入当前 Isaac Sim 5.1 + Lite3 V12 + MID-360/D435i 闭环的成本；
5. 许可证是否允许把代码或资产引入本项目。

本轮只检查仓库、文档和源文件，没有运行上游生成器或导入资产。所有候选均为
`surveyed`。

## 结论

**没有找到可直接放进当前 Isaac Sim 5.1、同时带森林资产、碰撞和 Lite3 的
一键仓库。** 但已经找到一组可落地的上游组合：

- **MAVS**：最完整的现成森林植被资产与生态配置来源；仓库实际包含 oak、
  pine、honey locust、fern、grass 等 OBJ/MTL/纹理，而不是空目录。
- **Forest3D**：最完整的 DEM -> 地形网格 -> 程序化森林 -> Gazebo SDF/glTF
  生成管线；但仓库的 `Blender-Assets/{tree,rock,bush,grass,soil}` 只有
  `.gitkeep`，没有可直接使用的植被模型。
- **NVIDIA Isaac Sim Procedural Forest Generator**：最接近 Isaac 的旧项目，
  仓库带 birch/spruce/pine/bush/rock USD；但无许可证文件、旧 API、Windows
  硬编码路径，而且代码只给地面应用碰撞，树木碰撞未建立。
- **MARSIM**：提供 `small_forest01cutoff.pcd` 等森林点云地图，适合激光和规划
  压力测试；点云不是物理地形，不能承担足地接触或树干碰撞。

因此首选实现不是移植某个完整模拟器，而是：**用 MAVS 的森林物种/外观和生态
分布作资产参考，在 Isaac 5.1 中原生建立地面与简化碰撞。**

## 候选比较

| 排名 | 候选 | 真正提供什么 | 主要问题 | 对本项目的定位 |
|---|---|---|---|---|
| 1 | [MSU MAVS](https://github.com/Mississippi-State-University-OTM/MAVS) | 随机生态系统、林道、真实植被 OBJ/纹理、LiDAR/相机仿真、ROS/ROS 2 wrapper | 独立车辆模拟器，不支持当前 Lite3 articulation；部分大型生态配置引用仓库外资产，需逐项核验 | **资产与森林分布首选**；不采用其车辆物理 |
| 2 | [Forest3D](https://github.com/unitsSpaceLab/Forest3D) | GeoTIFF DEM 转地形、Blender 转 glTF/SDF、程序化放置、优化碰撞网格、Gazebo Harmonic Docker | AGPL-3.0；不是 Isaac；仓库不附带树/灌木/岩石 Blender 资产 | **地形生成与放置逻辑参考**；代码与主线隔离 |
| 3 | [NVIDIA Isaac Sim Procedural Forest Generator](https://github.com/joevento/Nvidia-Isaac-Sim-Procedual-Forest-Generator) | birch/spruce/pine/bush/rock USD、纹理、随机地形和植被 UI | 无 LICENSE；2024 后未维护；旧 `omni.isaac`、硬编码 `D:/temp_downloads`、`interp2d`、非固定种子；仅地面碰撞 | 只做只读资产/视觉参考；许可证解决前不导入 |
| 4 | [MARSIM](https://github.com/hku-mars/MARSIM) | 十组 PCD 地图、森林点云、CPU/GPU LiDAR、MID-360 示例 | UAV/点云渲染器；没有可供 Lite3 接触的地形表面和碰撞体 | SCAN 点云回归图，不是物理场景 |
| 5 | [MAVS IFIT/soil adjacent work](https://github.com/unitsSpaceLab/Forest3D/tree/IFIT-2026) | Forest3D 的轮--土 Bekker-Wong 支路 | 面向轮式车辆，不是四足足--土模型 | 不纳入当前刚体森林 V4 |

Flightmare 和 PX4-Avoidance 也有无人机野外/森林演示，但没有比上述候选更适合
Lite3 的地面碰撞资产；PX4-Avoidance 已归档，因此不列为导入目标。

## 固定版本与原作者入口

核验时间：2026-08-14。

| 仓库 | 分支与固定 commit | 许可证 | 原作者入口/依赖 | 状态 |
|---|---|---|---|---|
| `Mississippi-State-University-OTM/MAVS` | `main` @ `e5b9913c34014e61b35924df4e7bf1855454f903`；2026-07-15 推送 | MIT | C++/CMake；独立 GUI/API；ROS/ROS 2 wrapper；JSON scene/ecosystem inputs | surveyed |
| `unitsSpaceLab/Forest3D` | `main` @ `5c3d331f96f7d526da082d0dc8f42a78ccf0f87a`；2026-06-12 推送 | AGPL-3.0 | Docker 推荐；GDAL、Blender 4.2、Gazebo Harmonic；`forest3d terrain/convert/generate/launch` | surveyed |
| `joevento/Nvidia-Isaac-Sim-Procedual-Forest-Generator` | `master` @ `9e5fcbe3fd11974f7b72f1781d522ae6e2b8734d`；2024-02-13 推送 | **未找到 LICENSE** | 旧 Isaac Sim extension；Python `noise`、SciPy、USD；无版本声明 | surveyed; license blocked |
| `hku-mars/MARSIM` | `ubuntu20` @ `2a287bb196eb35375636c3aa6ac6c6be45ebb1f3`；2025-10-25 推送 | GPL-2.0 | Ubuntu 20.04、ROS、PCL、Eigen、GLFW；`roslaunch test_interface single_drone_avia.launch` | surveyed |

## MAVS 为什么是当前最有价值的地形来源

MAVS 主仓库内已有以下可核验内容：

- `data/ecosystem_files/forest_simple.json`；
- `american_pine_forest.json`、`american_southeast_forest*.json`、
  `forest_with_cubes.json` 等多种生态配置；
- oak、pine tree、honey locust、fern、grass、bamboo 等 OBJ/MTL/纹理；
- scene 配置中的林道、地表、植被密度、物种高度和树径比例；
- `forest_simple` 使用仓库中实际存在的 oak、pine、honey locust、fern、
  oat grass 和 greater celandine 文件，可作为第一组自包含资产。

`forest_simple` 的原始配置面向车辆，例如林道宽度为 4.5 m；不能原样当 Lite3
基准。迁移时应保留物种和视觉分布，按 Lite3 尺寸重新设计通行间距。

根目录 MIT 许可证覆盖仓库，但正式复制大型 OBJ/纹理前仍应检查每个第三方模型
是否有额外来源或署名要求；这一点尚未完成人工许可证复核。

## 推荐的 Isaac Forest V4 构造

### 视觉层

- 从 MAVS 的自包含 `forest_simple` 子集开始：oak、pine、honey locust、fern、
  grass；经过许可证复核后转换为 USD。
- 叶片、草和蕨类默认只参与 RGB/深度/LiDAR 渲染，不直接生成高精三角碰撞。

### 物理层

- 地面：Isaac 原生 height field/trimesh，固定 seed、坡度和粗糙度；可用
  Forest3D 附带 DEM 作为形状参考，但不复制其 AGPL 实现到主线。
- 立木：视觉树模型 + 独立 cylinder/capsule trunk collider。
- 倒木：横放 cylinder/capsule；岩石使用 convex hull 或简化 primitive。
- 灌木：视觉/传感器遮挡层与可选低刚度风险区分开，避免把每片叶子设为刚体。
- 所有碰撞体、视觉资产和随机放置分别记录，防止“画面有树但机器人穿树”。

### 首批四个场景

| 场景 | 地形组成 | 主要目的 |
|---|---|---|
| T1 林道 | 起伏地面、两侧树阵、草地、宽度渐缩 | 长距离跟踪与树干点云 |
| T2 稀疏坡林 | 横坡、随机树径、岩石、少量蕨类 | 规划几何 + 足地物理 |
| T3 密林灌木 | 高密树干、视觉灌木、遮挡、曲折窄缝 | 未知区、遮挡与重规划 |
| T4 倒木林地 | 倒木、裸根近似、石块、低枝和死胡同 | 3D 碰撞、回退和腿部卡阻风险 |

## 推荐的第一复现目标

在 Dr Sun 选择后，第一步应是 **MAVS terrain-asset smoke**，不是替换规划器：

1. 将固定 MAVS revision 作为只读上游源导入 dated reference；
2. 只取 `forest_simple` 所需的地表、oak、pine、honey locust、fern、grass 资产；
3. 在 5070 Ti 的 Isaac Sim 5.1 中转换并显示一小块 20 m x 20 m 场景；
4. 为地面和三个树种建立独立简化碰撞，并用 Lite3 做静态接触/穿透检查；
5. 输出 GUI 视频、USD/资产/许可证清单、碰撞 readback、MID-360 点云和 D435i
   深度帧；经 Dr Sun 人工看图后再扩展四个场景。

该 smoke 成功只能标记为“terrain assets integrated”；在 SCAN 完成路线之前，
不能称为森林导航 validated。

## 未解决项

- MAVS 植被 OBJ/纹理的逐资产来源与许可证仍需人工复核。
- 未验证 MAVS OBJ 的透明叶片材质能否在 Isaac Sim 5.1 中无损转换。
- 未验证 20 m x 20 m 场景在当前 5070 Ti 上同时启用 Lite3、MID-360 和 D435i
  后的帧率与显存。
- Forest3D 原始 Docker 流程尚未运行；其仓库不含植被资产，不能把 README
  截图当作本地可生成同等画面的证据。
- 旧 NVIDIA 森林扩展的资产许可证和树木碰撞均未建立，不作为第一导入目标。
