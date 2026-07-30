---
origin: ai+web
reviewed: false
date: 2026-07-26
status: surveyed
---

# Lite3 factory LiDAR 版完整官方三维资料可获得性调查

## 调查问题

本轮只回答一个问题：公开官方资料中，是否存在一份能够同时表达 Lite3 本体、
factory LiDAR 支架、相机、Interface/工控机及真实装配关系的完整原始三维总装，
例如 CAD、STEP 或 URDF。

## 结论

截至 2026-07-26，在本轮核验的官方资料中未发现上述完整总装。现有证据分散在
四类资料中：Lite3 本体模型、LiDAR 版外观与尺寸手册、Lite3 Venture 的
FAST-LIVO2 扩展件，以及 Mid-360/D435i 独立器件模型。它们不能在没有额外装配
证据的情况下拼接成“官方 factory LiDAR 总装”。

该结论只说明本轮检查的公开官方来源中未发现完整总装，不证明制造商内部不存在
未公开 CAD。

## 官方资料与证据边界

| 资料 | 已确认内容 | 不能支持的结论 |
|---|---|---|
| `DeepRoboticsLab/deep_robotics_model` | Lite3 本体 URDF/DAE | 不包含 factory LiDAR 上装、支架、相机、Interface/工控机及其装配关系 |
| Jueying Lite3 LiDAR User Manual CE V1.0.7 | LiDAR 版产品外观、部件名称与 610 × 370 × 496 mm 总体尺寸 | 不提供上装 CAD、安装孔位、装配坐标或完整 URDF/STEP |
| `DeepRoboticsLab/fast-livo2-deep-robotics` | Lite3 Venture FAST-LIVO2 扩展方案；J17A、J20A、S410、BZ20、AGX STEP 与安装视频 | README 的硬件扩展边界为 Venture only；不能当作 factory LiDAR V1.0.7 总装 |
| Livox Mid-360 STEP | Mid-360 独立器件几何 | 不给出其在 Lite3 上的官方支架和装配坐标 |
| RealSense D435i CAD/ROS mesh | D435i 独立器件几何 | 不给出其在 Lite3 factory LiDAR 版上的官方安装关系 |
| DEEP Robotics downloads | 官方下载入口，本轮用于交叉检查公开资料 | 本轮没有在该入口发现完整 factory LiDAR 总装 CAD/STEP/URDF |

## 不能采用的替代物

以下内容不构成完整官方三维证据，不能标成官方总装：

- 混用不同 Lite3 版本或 Venture 扩展件拼出的自制候选；
- 依据产品图估算工控机、相机或 LiDAR 的位置；
- 没有官方孔位、坐标系或装配说明时自行设计支架；
- 把 Mid-360、D435i 等独立器件 CAD 与 Lite3 本体模型合并后省略
  “非官方重建”标签。

因此，本轮此前产生但缺少上述证据的自制方案不纳入项目知识库结论。

## 官方来源

- [DeepRoboticsLab/deep_robotics_model](https://github.com/DeepRoboticsLab/deep_robotics_model)
- [Jueying Lite3 LiDAR User Manual CE V1.0.7](https://www.deeprobotics.us/wp-content/uploads/2025/08/Jueying-Lite3-LiDAR-User-Manual-CE-V1.0.7-0.pdf)
- [DeepRoboticsLab/fast-livo2-deep-robotics](https://github.com/DeepRoboticsLab/fast-livo2-deep-robotics)
- [DEEP Robotics downloads](https://www.deeprobotics.us/downloads/)

## 可继续取得几何资料的路径

1. 向 DEEP Robotics 或其授权渠道索取 factory LiDAR 版总装 CAD，以及支架图、
   孔位、BOM、坐标系和版本号；只有来源与版本可追溯时，才能称为官方总装。
2. 对真实 LiDAR 版进行测量或三维扫描，形成明确标注为“实测重建、非官方原始
   CAD”的项目模型，并保存设备版本、测量方法和误差记录。

## 状态边界

- `surveyed`：已检查上述官方资料并记录它们各自能支持的边界。
- 本轮只完成公开资料核验；没有运行上游流程、接入三维资产或执行项目验收测试。
