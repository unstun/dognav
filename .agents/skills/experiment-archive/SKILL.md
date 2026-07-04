---
name: experiment-archive
description: |-
  Lite3 实验归档 SOP: 把训练、推理、评估 run 记录成可复查但不死板的 capsule, 保住关键证据, 允许按实验特点自由组织叙述。
  触发: Dr Sun 说 "实验归档/归档记录/记录 checkpoint/同步产物/训练结果归档/多场景评估归档", 或 AI 完成远端训练/推理后需要关闭实验。
argument-hint: "[实验 ID 或归档目标, 如 nav_pointgoal_baseline_seed42]"
user-invocable: true
context: inline
---

# Lite3 实验归档

> 受众: Claude Code、Codex App/CLI、Cursor 主 session。目标是让 Dr Sun 一眼看懂实验身份、产物位置、claim 边界; 不要求每次都填满表格。

## 0. 先定身份

先用一句人话给实验贴标签。可以是自然语言, 不强制固定格式; 禁止只写版本号。

例: `point-goal baseline 是第一轮 nav 合同下的 256-env smoke, 主权重 model_0800.pt, 不能当 sim-to-real 结论。`

## 1. 最小必填事实

归档最少要说清这 6 件事, 其余自由发挥:

- 它是什么实验, 不是只写代号。
- 从哪里来: parent checkpoint / source snapshot / contract, 能找到多少写多少。
- 跑了什么: task ID、训练或推理命令、conda env; 找不到就写缺失原因。
- 产物在哪: 主 checkpoint、日志、TensorBoard、视频或关键图。
- 结果怎么看: 推荐用哪个, 哪个不推荐, 为什么。
- 边界是什么: 能 claim 什么, 不能 claim 什么。

可以加自己的叙述、截图观察、失败分析、下一步判断; 不必为了模板而写空话。

## 2. 证据顺序

默认先本地、再远端、最后联网:

- 本地真源: repo、git hash、source snapshot、contract、`.pipeline/experiments/`。
- 远端事实: host、run dir、命令、env、stdout/stderr、TensorBoard、checkpoint、配置、视频。
- 联网事实: 只查外部规范、论文先例、工具行为或官方文档。

## 3. 结果包门槛

归档不是只写 `.pipeline` 台账。`status: archived` 的实验必须有一个本地结果包:

```text
artifacts/<experiment_id>/
```

训练/复现实验的底线:

- `tracked_checkpoints/`: 至少一个 `.pt` 或 `.pth` 主权重。
- `tracked_logs/`: stdout/stderr 或等价完整运行日志。
- `tensorboard/`: event file 或能解释曲线来源的日志。
- `manifests/`: 命令、source hash、sync/checksum 记录。
- 以上关键文件必须被 git 跟踪; 如果太大不能进 git, `status` 必须写 `incomplete`, 并明确写缺失文件、原因、替代校验方式。

推理/评估实验可以按实际情况换成 `videos/`、`frames/`、`plots/`, 但也必须有真实文件, 不能只有台账路径。

## 4. 双端同步门

本地 repo 是唯一代码真源; 远端目录只是运行副本。

- 训练或推理结束后, 立刻同步回本地: `.pt/.pth`、TensorBoard、stdout/stderr、命令、`env.yaml/agent.yaml`、视频、关键帧、source-hash manifest。
- 新实验优先放: `artifacts/<experiment_id>/{tracked_checkpoints,tracked_logs,tensorboard,videos,frames,manifests}/`
- 如果 checkpoint 或完整日志缺失, `status: incomplete`; 不得写成已复现或已完成。
- 如果文件太大不能提交, 当场报告给 Dr Sun, 并在台账写明没有纳入 git 的具体原因和替代校验方式。

## 5. 联网规则

联网只服务于外部事实, 不覆盖本地实验事实。

- 需要查实验追踪规范、论文先例、工具行为或当前官方文档时才联网; 普通本地归档不用硬联网。
- Claude Code 优先 `smart-search-cli`; 没有则 WebSearch/WebFetch。
- Codex App/CLI 优先当前可用 web 工具; 若只能离线, 在台账写 `network: skipped` 和原因。
- 只引用官方文档、论文原文、项目仓库或明确来源; 搜索摘要不能直接当证据。
- 用了联网就记录 URL、访问日期、该来源支持的具体 claim。

## 6. 写归档台账

复制模板: `templates/experiment_record.md`; 目标路径是 `.pipeline/experiments/YYYY-MM-DD/<experiment_id>.md` 和 `artifacts/<experiment_id>/`。

模板只是起点: 可以删掉不相关栏目、增加实验特有栏目、把表格改成段落。不要删掉最小必填事实。

## 7. 校验

归档后运行:

```bash
python .agents/skills/experiment-archive/scripts/validate_experiment_archive.py .pipeline/experiments/YYYY-MM-DD/<experiment_id>.md
```

默认校验会检查最小骨架、`artifacts/<experiment_id>/` 结果包、关键证据类别和 git 跟踪状态。需要严格审计时加 `--strict`。

还要手工检查: `git status --short` 只含本次归档; 未知项要写明原因; 本地关键路径可 `ls`; checkpoint/video/log 尽量记录 sha256。

## 8. CLI 适配

| 环境 | 执行方式 |
|---|---|
| Claude Code | 可直接读写文件、联网、SSH；缺关键信息时用 AskUserQuestion 问 Dr Sun。 |
| Codex App/CLI | 直接按本 skill 执行；没有问答工具时用简短中文问题确认; 远端长任务遵守 `remote-ssh`/`remote-experiment` 的 Source of Truth + Sync Gate。 |
| Cursor | 主 session 只协调和生成任务包；长训练/大同步交给终端或 Codex App, 回贴结果后再归档。 |

Claude Code 也有镜像入口: `.claude/skills/experiment-archive/SKILL.md` 和 `/experiment-archive` 命令。唯一规范源仍是本目录, 避免两边规则漂移。

## 9. 结束语格式

最后只给 Dr Sun 三件事: 归档文件路径、主/不推荐 checkpoint、一句话 claim 边界。
