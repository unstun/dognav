# .pipeline/ — 项目知识库

`.pipeline/` 存放长期有效的结构化项目知识，不按天归档，不自动过期。它与 `bigmemory/` 互补：`bigmemory/` 管当前会话状态，`.pipeline/` 管可复查事实、合同、台账和评审。

## 数据库清单

| 目录 | 用途 | 格式 |
|---|---|---|
| `terminology/` | 术语规范表 | 单文件 Markdown 表格 |
| `literature/` | 文献库索引 | Markdown |
| `survey/` | 调研主题、结论和出处 | 每个主题一个 `.md` |
| `experiments/` | 实验台账 | 每轮实验一个 `.md` |
| `contracts/` | Research Contract 预注册 | 每个实验主题一个 `.md` |
| `codex_tasks/` | Codex 手动任务包归档 | 每个任务包一个 `.md` |
| `goals/` | 自主执行 goal 定义 | 每个 goal 一个 `.md` |
| `plans/` | 实施计划 | 每个计划一个 `.md` |
| `audits/` | 代码/产出验收审计 | 每次审计一个 `.md` |
| `reviews/` | 同行评审记录 | 每次评审一个 `.md` |
| `heartbeats/` | 远端任务心跳日志 | 日志文件 |
| `incidents/` | 事故记录 | 每个事故一个 `.md` |

## 当前入口

| 主题 | 入口 |
|---|---|
| 术语规范 | `terminology/terminology.md` |
| Research Contract 规则 | `contracts/README.md` |
| nav 文献索引 | `literature/README.md` |
| nav 调研记录 | `survey/README.md` |
| nav 实验台账 | `experiments/README.md` |

## 维护原则

- `draft` 文档可以修改；`approved` 或 `frozen` Contract 不得原地改。
- 任何 claim 必须能回到 Contract、代码、日志、原文或本地文件。
- walking 仓库内容只能作为 source reference，不能作为 nav 当前结论。
