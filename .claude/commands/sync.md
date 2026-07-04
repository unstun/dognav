---
description: 强制同步项目状态到 bigmemory 热区和 .pipeline 知识库
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Lite3 机器狗导航 DRL Conductor。用户调用此命令是因为项目状态文档没有及时更新。你的任务是**全面刷新热区状态 + 补全知识库**。

## 第一步：读取所有原始数据

一次性读取所有状态源，获取完整上下文：

```
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
bigmemory/热区/近期改动.md
.pipeline/literature/index.md
.pipeline/experiments/                    # 扫描所有台账文件
.pipeline/survey/                         # 扫描所有调研文件
.pipeline/terminology/terminology.md
3_paper/main.tex                          # 论文当前状态
2_experiment/nav_baselines/               # nav baseline 子项目
2_experiment/source_references/           # walking / external source references
```

## 第二步：向用户确认遗漏的进展

用 `AskUserQuestion` 询问：

> **进度同步**
>
> 我已读取所有文件，准备更新状态文档。
>
> 请简述一下**文档中没有记录但实际已完成的事情**（如果有）：
> - 例：「PPO 基线训练完成，成功率 78%」
> - 例：「调整了地形生成方案，改为程序化随机森林」
> - 例：「没有遗漏，只是文档没更新」

选项：
- `没有遗漏，直接从现有文件同步`
- `有遗漏，我来描述`

如果用户选"有遗漏"，用纯文字追问具体内容，收集后再继续。

## 第三步：更新 bigmemory/热区/状态简报.md

综合所有信息，**完整重写**状态简报：

```markdown
# 项目状态简报
> 最后更新：[ISO 日期时间]

## 当前在做什么
- [从实验台账、论文、调研文件中提取当前活跃工作]

## 关键上下文
- [项目基本信息：baseline 子项目、当前 Python module、机器人 Lite3、仿真平台、算法选型等不变信息]
- [当前阶段、关键技术选型等]

## 近期警告
- [需要注意的风险项或阻塞项]
```

## 第四步：补全 .pipeline/ 知识库

检查以下是否有遗漏，按需补全：

| 检查项 | 文件 | 动作 |
|--------|------|------|
| 新实验是否有台账 | `.pipeline/experiments/` | 缺则新建 `YYYYMMDD_<topic>.md` |
| 新文献是否已索引 | `.pipeline/literature/index.md` | 缺则追加行 |
| 新调研是否有结论 | `.pipeline/survey/` | 缺则新建 `<主题>.md` |
| 术语是否有新增 | `.pipeline/terminology/terminology.md` | 缺则追加行 |

## 第五步：确认完成

写完后，用 `AskUserQuestion` 确认：

> **同步完成**
>
> 已更新：
> - `bigmemory/热区/状态简报.md` — 刷新项目状态
> - `.pipeline/` — 补全缺失的知识库条目
>
> 接下来？

选项：
- `继续当前任务`
- `查看更新后的进度（/plan）`
- `没事了`
