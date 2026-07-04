# Evidence-First Research Iteration Examples

## v9b 失败后拆 command 因素

```text
实验：
Wave C v9b command curriculum quick-test

预注册依据/Contract：
.pipeline/contracts/wave_c_v9b_command_curriculum_quicktest_v5.md

Contract 状态：
approved

运行记录：
.pipeline/experiments/2026-05-29/wave_c_v9b_command_curriculum_quicktest.md

基线：
v8i model_1998

本轮改动：
command resampling 与 lin/yaw command curriculum

保持不变：
reward、terrain、observation、network、PPO、domain randomization

评估设置：
32 env，1000 steps，seed 42，active_curriculum_terms 为空

success signal：
所有 hard gates 通过，且至少两个 screening signals 改善

failure signal：
任一 hard gate 失败，或触发 Contract 中独立 failure signal

原始指标：
actual_xy_norm=0.309，speed_error=0.597，bad_orientation_2=32，all_feet_airborne_ratio=0.083。

可视化/日志：
model_2997_summary.json、model_2997_timeseries.csv、model_2997_play_400.mp4。

异常：
训练标量看起来健康，但推理 locomotion hard gates 失败。

H1：
command curriculum 起点过低，训练早期大量命令接近原地站立，策略学成低速保守行为。

支持证据：
A：v9b 指标显示速度和姿态明显退化。
已核验：是
来源：.pipeline/experiments/2026-05-29/wave_c_v9b_command_curriculum_quicktest.md

B：本项目 lin command curriculum 的 range_multiplier 起点是 0.1。
已核验：是
来源：2_experiment/baseline_rebuild/robot_lab_lite3_isaaclab_stairs_v8_two_phase/src/robot_lab_lite3_stairs_v8_two_phase/tasks/__init__.py:817

B：命令代码会把 xy 范数小于等于 0.2 的命令清零。
已核验：是
来源：2_experiment/source_references/fan_ziqi_external/robot_lab/upstream/source/robot_lab/robot_lab/tasks/manager_based/locomotion/velocity/mdp/commands.py:47

C：fan-ziqi Lite3 配置默认关闭 command_levels_lin_vel 和 command_levels_ang_vel。
已核验：是
来源：2_experiment/source_references/fan_ziqi_external/robot_lab/upstream/source/robot_lab/robot_lab/tasks/manager_based/locomotion/velocity/config/quadruped/deeprobotics_lite3/rough_env_cfg.py:155

反对证据：
v9b 同时改了 resampling、lin curriculum、yaw curriculum，不能确认单一因素。

缺失证据：
缺少只改 lin curriculum、只改 yaw curriculum、只改 resampling 的单因素实验。

什么结果会证明 H1 错：
只开 lin curriculum 后速度和姿态仍接近 v8i，说明低速退化不主要来自 lin command curriculum。

H2：
feet_air_time.weight=5.0 可能过强，让 v8i 学会前进的同时带来过长腾空。

支持证据：
A：v8i 会走但 all_feet_airborne_ratio 偏高。
已核验：是
来源：artifacts/wave_c_v9_complete_probe_20260529_v4/model_1998_summary.json

B：本项目 v8i 相比 v8h 的关键新增项是 feet_air_time.weight=5.0。
已核验：是
来源：2_experiment/baseline_rebuild/robot_lab_lite3_isaaclab_stairs_v8_two_phase/src/robot_lab_lite3_stairs_v8_two_phase/tasks/__init__.py:784

反对证据：
v9b 没有修改 feet_air_time，不能用 v9b 结果证明该项是主因。

缺失证据：
缺少只改 feet_air_time 的对照。

什么结果会证明 H2 错：
只降低 feet_air_time 后腾空指标不下降，或速度明显退化。

资格建议：
可提议拆解 v9b command 因素；暂缓 feet_air_time 修改。

下一轮最小实验：
问题：lin command curriculum 是否单独导致低速退化。
假设：range_multiplier=0.1 的 lin command curriculum 会制造近零命令并损伤 locomotion。
只改：打开 command_levels_lin_vel。
不改：resampling_time、command_levels_ang_vel、reward、terrain、observation、PPO。
基线：v8i model_1998。
评估套件：沿用 v9b probe。
预期结果：如果速度和姿态退化，H1 得到支持；如果接近 v8i，继续拆 yaw 或 resampling。

暂缓修改：
feet_air_time、history、teacher-student、base-height。

Contract 判定：
failure

机制解释判定：
insufficient evidence。v9b 说明 command 组合有问题，但还没有区分 lin、yaw 和 resampling。

决策授权：
普通模式需 human-approved。/goal 模式需 goal-preauthorized 或 3 个只读 subagent 投票通过。

不要重复：
不要把 command resampling、lin curriculum、yaw curriculum 和 reward 一起改。
```

## 通用模板

```text
实验：
预注册依据/Contract：
Contract 状态：
运行记录：
基线：
本轮改动：
保持不变：
训练/分析设置：
评估设置：
success signal：
failure signal：
原始指标：
可视化/日志：
异常：

候选假设：
H1：
机制：
支持证据：
反对证据：
缺失证据：
什么结果会证明 H1 错：

证据核验：
等级：
内容：
已核验：是/否
来源：

修改资格：
准备建议什么：
是否只改一个主要因素：
证据是否覆盖当前项目结果：
证据是否覆盖代码/配置机制：
证据是否有外部来源或历史实验支持：
反证是否足够严重：
能否被下一轮实验证伪：
资格建议：可提议 / 只能补证据 / 暂停

下一轮最小实验：
问题：
假设：
只改：
不改：
基线：
评估套件：
预期结果：
如果结果 A：
如果结果 B：
如果结果 C：
暂缓修改：

决策授权：
human-approved / goal-preauthorized / agent-voted / needs-human-review / blocked-by-evidence

/goal 投票记录：
subagent 1 vote：
subagent 2 vote：
subagent 3 vote：
dissent：

Contract 判定：
success / failure / partial / not-applicable

机制解释判定：
explained / contradicted / insufficient evidence

归档草稿：
实验：
事实：
证据核验：
Contract 判定：
机制解释判定：
学到的东西：
被否定的解释：
仍缺的证据：
下一轮最小实验：
决策授权：
不要重复：
应写入位置：
```
