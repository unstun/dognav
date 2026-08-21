---
origin: ai+web
reviewed: false
---

# v2.0.1 点云分流与 SCAN 几何验收审计

- 审计日期：2026-08-21 PDT
- 审计对象：`office-v2.0.1-go2-geometry-preflight` / `upstream_go2_reference`
- 任务：`08-20-v2-0-1-cloud-traversability`
- 运行代码提交：`2259afe1964db1495206d67f97e134a9bdf6d5b9`
- 审计时仓库 HEAD：`791e75c`
- 阶段：实验 + 分析
- 总结论：**新 v2.0.1 平地 profile 有条件通过；整个版本暂不通过验收，任务保持 `in_progress`。**

> [模型回退] 本机 Codex CLI `0.142.3` 不支持主会话模型
> `gpt-5.6-sol`；改用同级可用模型 `gpt-5.5` 做只读知识库质量门控，结果
> `PASS`。门控未修改项目文件。

## 1. 为什么做这次独立验收

本次改动要同时解决两件容易混在一起的问题：一是让 RViz 持续显示真实
环境点云，包括地面；二是让 SCAN 只接收经过几何地形过滤的规划云，避免
把连续地面直接当作占据障碍。另一个交付要求是保留视频母版，并生成小于
10,000,000 bytes、可直接播放的独立压缩副本。

实现窗口已经给出通过结论。本轮不修改实现，只从本地代码、测试记录、
运行产物、清单和视频重新核对，防止把“新 profile 的平地短预检通过”误写
成“旧模式没有回归”或“复杂地形已经验证”。

## 2. 已复核通过的证据

### 2.1 新 profile 的 raw/planner 点云分流

- `office_v2_0_1_go2_geometry_preflight02` 中，Isaac 生成与 Foxy 发布均为
  101 帧，scan ID 连续为 1--101，`telemetry_overwrite_count` 最大值为 0。
- `/quad_0/cloud_raw` 供 RViz 显示，保留有限且在量程内的地面与环境点；
  `/quad_0/cloud` 供 SCAN，移除连续局部最低面。两云来自同一次扫描，共享
  scan ID、时间戳和坐标系。
- 每帧审计满足 `raw_point_count = filtered_ground_point_count +
  planning_point_count`。保守保留点是 planning 云中的子集，不应再次加到
  该等式右侧。
- 运行汇总的 raw 点数范围为 16,704--16,882，过滤地面点数范围为
  3,641--6,923，planning 点数范围为 9,894--13,122，保守保留点数范围
  为 5--287。
- RViz 合约为 `/quad_0/cloud_raw`、Decay `0.0`；其含义是保留最新一帧
  真实点云直到下一帧替换，不是插值、重放或额外发布点云。

主要证据：

- `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/results/office_v2_0_1_go2_geometry_preflight02/dual_cloud_scan_audit.jsonl`
- `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/results/office_v2_0_1_go2_geometry_preflight02/postprocess_recovery_manifest.json`
- `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/results/office_v2_0_1_go2_geometry_preflight02/live_pointcloud_continuity_audit_retry02.json`
- `integration/lite3_sim_bridge/config/foxy_bridge_upstream_go2_reference.yaml`
- `integration/lite3_sim_bridge/lite3_sim_bridge/foxy_bridge_node.py`

### 2.2 点云频率的正确解释

- 101 帧审计的仿真时间频率为 `10.000000200000004 Hz`，仿真时间相邻间隔
  约 0.10 s，符合 MID-360 当前 10 Hz 配置。
- 同一运行的墙钟到达间隔中位数为 1.953 s，按 101 帧覆盖的实际墙钟时长
  折算约 `0.539 Hz`。这是仿真低实时率下的墙钟表现，不能反过来判定传感器
  仿真频率错误。
- 因 RViz Decay 为 0，低墙钟频率时画面仍保留最新真实帧，所以“持续可见”
  不等于“墙钟每秒更新 10 次”。

### 2.3 借用参数的来源和边界

官方 SCAN-Planner commit
`348e8a590a50a5a6bbab8d8c6dcfd171f009be26` 的
[`advanced_param.xml`](https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_manage/launch/advanced_param.xml)
给出 Go2 的五项碰撞包络值：半径 `0.25 m`、偏移 `0.18 m`、机身高度
`0.40 m`、z 上/下膨胀 `0.10/0.10 m`。本地独立 profile 精确借用了这
五项值；没有借用上游 `0.75 m/s` 最大速度和 `3.5 m` horizon。本地继续
使用 Lite3 `0.50 m/s` 与 Office `8.0 m` horizon。

这些是 Go2 参考参数，不是 Lite3 真机标定结果，也不能据此推出 Lite3 的
坡度、台阶或通过性极限。

### 2.4 测试与构建复核

- 本轮重跑针对性本地测试：86 项通过。
- 本轮重跑本地全量 bridge 测试：153 项通过，2 项按环境跳过。
- Trellis task validator、revision ledger validator、Python compileall、
  shell 语法和 diff whitespace 检查通过。
- 归档的 Foxy 证据显示：针对性 bridge 测试 25 项通过，SCAN 四个 CTest
  target 通过。
- Foxy bridge 整包未全绿：钉住镜像缺少 `torch`，既有测试收集失败。
  因此只能写“受影响 targeted 测试通过”，不能写“Foxy 整包通过”。

### 2.5 小于 10 MB 的传输视频

独立传输实体
`office_review_third_person_rviz_4k_transfer_under10mb.mp4` 已复核：

- 9,515,787 bytes，严格小于 10,000,000 bytes；
- H.264 High / `yuv420p` / BT.709，3840x1080，25 fps；
- 251 帧，10.04 s，全量解码通过，帧数、时长、分辨率和帧率与母版一致；
- SSIM `0.972493`；母版及旧传输版哈希未改变；
- SHA-256：
  `2b6009e80ba12c109fd6aee7fadfa2eb190e4d8e0369ac495d02152c246400be`。

本轮人工抽样查看约 1 s、5 s、9 s 画面，双视角中的 RViz 点云均可见；
自动审计还记录 251/251 帧可见、最长连续不可见帧数为 0。该抽样只是验收
辅助，不代替 Dr Sun 持有的 AC55 人工门。

主要证据：

- `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/results/office_v2_0_1_go2_geometry_preflight02/office_review_third_person_rviz_4k_transfer_under10mb_validation.json`
- `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/results/office_v2_0_1_go2_geometry_preflight02/live_pointcloud_continuity_audit_retry02.json`

## 3. 阻断验收的问题

### 3.1 旧默认 profile 存在“可能没有点云显示”的回归

默认 `legacy_planner_v1` 仍发送 V1 单云，Foxy 只发布 `/quad_0/cloud`；但
共享 RViz / voxel 显示链已固定监听 `/quad_0/cloud_raw`。因此新 profile
通过不能证明旧默认模式兼容：旧模式可能正常规划，却在 RViz 中没有点云。

接受整个 v2.0.1 前，应让显示 topic 随 profile 选择，或为 legacy 提供明确
fallback，并添加从默认启动入口覆盖到 RViz topic 的回归测试。修复时不能
把 planner 云改名伪装成 raw 云，也不能让 SCAN 订阅 raw 云。

### 3.2 完整运行实体尚未回收到本地

`remote_recursive_sha256.txt` 列出 130 个远端实体。本轮逐项检查本地路径
和实际 SHA-256：66 个匹配、63 个缺失、1 个不匹配；不匹配项为
`closed_loop.mp4`，远端期望哈希为
`c6283be80e3326b9733ce9883ebcc837502265eae8da9bbcb932b1bfdf942f1e`，
本地实际哈希为
`33e5e94a4dd1e9e9ea4f46e8a767e93956a812301cc5238518e9735015355929`。

因此 `remote_recursive_sha256.txt` 只是远端清单证据，不能当作 130 个实体
已在本地。`implement.md` 的“完整 artifact tree 本地回收并证明递归哈希
一致”仍未完成。

### 3.3 项目顶层状态有漂移

- `AGENTS.md` 的 Current Boundary 仍写 `office-r2.0.0-preflight`。
- 父任务 `08-17-office-crowd-review-visual-r2/task.json` 仍记录旧 working
  revision / latest run；当前热区和 experiment README 已进入
  `office-v2.0.1-go2-geometry-preflight`。

这些入口同时声称是状态来源，却不一致。验收前需要在不覆盖历史 revision
的前提下统一当前 working revision、latest run 和 claim boundary。

### 3.4 遥测 connect timeout 参数没有真正独立生效

`foxy_bridge_node.py` 声明 `connect_timeout_seconds=1.0` 与
`telemetry_receive_timeout_seconds=10.0`，但遥测 `FrameStreamClient` 只以
receive timeout 构造；该类同一个 timeout 同时用于 `socket.create_connection`
和后续 socket I/O。结果是遥测建连实际使用 10 s，声明的 1 s connect
timeout 没有进入 telemetry client。它不是本次平地通过的否定证据，但属于
配置语义与实现不一致，应拆分或加测试。

## 4. 尚未执行，不得外推

- 非平地 reference-path 短预检未获 Dr Sun 单独授权，未运行。
- 没有新 AC54；AC55 尚未由 Dr Sun 决定。
- `accepted_revision` 与 `formal_candidate` 仍为 `null`。
- 没有真机验证，也没有 Lite3 自身几何标定或通过性极限验证。
- 10.04 s 平地短预检没有到达完整 Office 导航目标，不能写成完整任务成功。

## 5. 最终判定与下一次回退依据

### 有条件通过的范围

仅对 `upstream_go2_reference` 的 10.04 s 平地短预检，可以确认：同扫描
raw/planner 分流、raw 点云持续可见、SCAN 只接规划云、五项 Go2 参数来源
可追溯，以及小于 10 MB 的传输视频合约均有直接证据。

### 当前不通过的范围

整个 v2.0.1 不能验收：旧默认 profile 显示兼容回归未解决，完整实体回收
与递归哈希一致未完成，顶层状态源漂移，非平地/AC54/AC55/真机均未验证。
任务应保持 `in_progress`。

### 回退锚点

- 运行行为提交：`2259afe1964db1495206d67f97e134a9bdf6d5b9`。
- 若确认需要整体撤回该运行行为，精确回退命令为
  `git revert 2259afe1964db1495206d67f97e134a9bdf6d5b9`。
- 回退实现不应删除本次失败/通过 run、视频母版、压缩副本、清单、哈希、
  测试日志或本审计；这些是解释“为什么改、改了什么、为什么又回退”的
  历史证据。
- 本审计只记录事实和验收边界，不授权执行回退、非平地仿真、正式训练或
  真机动作。
