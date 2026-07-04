---
description: 让 Codex 对主 AI（Claude）的所有改动做同行审查——代码/论文/实验/文档全量覆盖
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Lite3 机器狗导航 DRL Conductor。此命令让 **Codex 稳定审查主 AI（Claude）做出的一切改动**——包括但不限于代码、论文、实验台账、pipeline 文档、bigmemory。走 companion 的 `adversarial-review` 通道（app-server JSON-RPC，不走 MCP 60s 限时路径）。

## 第一步：自动采集改动范围

并行跑以下 Bash 命令摸清仓库状态：

```bash
git status --porcelain
git log --oneline -10
git diff --stat HEAD~1..HEAD
git diff --stat
```

判断：
- 有未提交改动 → 默认建议 `working-tree`
- 无未提交改动但最近 1~3 次 commit 是主 AI 动作（commit message 含 `auto-backup before edit` 等）→ 建议 `branch --base HEAD~N`
- 存在特性分支且偏离 main → 建议 `branch --base main`

## 第二步：用 AskUserQuestion 确认审查范围

展示自动采集到的改动摘要（改了哪些文件、涉及哪些目录），然后选：

- `审未提交改动（--scope working-tree）`
- `审最近 1 次 commit（--scope branch --base HEAD~1）`
- `审最近 N 次 commit（需 Dr Sun 指定 N）`
- `审当前分支 vs main（--scope branch --base main）`
- `审指定 base（Dr Sun 提供 ref）`
- `取消`

## 第三步：用 AskUserQuestion 确认审查侧重

```
选项：
- 全面审查（不指定 focus，Codex 自由发挥）
- 代码正确性与安全（bug / 边界 / 性能 / 风险）
- 论文写作质量与数据一致性（核对 3_paper/main.tex vs .pipeline/experiments/）
- 实验设计与 Contract 一致性（核对实验记录 vs .pipeline/contracts/）
- 术语规范一致性（对照 .pipeline/terminology/terminology.md）
- 自定义 focus（Dr Sun 输入一段话）
```

若选具体 focus，拼 focus text 时同时附上上下文指示：例如术语审查 focus 文本应写 "Check terminology compliance against .pipeline/terminology/terminology.md"。

## 第四步：调用 codex-companion.mjs adversarial-review

用 Bash 工具执行（`run_in_background=true`，背景跑避免主 session 阻塞）：

```bash
node "/Users/sun/.claude/plugins/cache/openai-codex/codex/1.0.2/scripts/codex-companion.mjs" \
  adversarial-review \
  --wait \
  --scope <working-tree|branch> \
  [--base <ref>] \
  [--model <model>] \
  "<focus text>"
```

说明：
- `--wait` 前台等结果（companion 内部仍走 app-server JSON-RPC，无 60s 超时限制）
- `--scope` 合法值：`auto | working-tree | branch`
- `--base` 仅在 `--scope branch` 下生效
- focus text 是 positional 参数，不加 `--focus` 前缀
- 全面审查时 focus text 留空

用 Monitor 或定时 Read 输出，产出后进入下一步。若 5 分钟无输出，停止背景任务，换 `--scope auto` 或缩小范围重试。

## 第五步：解析 Codex 返回的 findings

从 Codex 输出中抽取 finding 列表，按严重度归档：
- **Critical**：必须修（数据错误 / 安全漏洞 / 论文 claim 与 contract 冲突 / bug）
- **Major**：强烈建议修（实验台账与论文数据不一致 / 术语违规 / 逻辑缺陷）
- **Minor**：优化建议（措辞 / 结构 / 注释缺失）

如果 Codex 返回格式不是 finding list 而是散文式 review，主 AI 自行切分为条目。

## 第六步：逐条与 Dr Sun 讨论（禁止批量应用）

按严重度从高到低，每条 finding 用 `AskUserQuestion`：

> **[Critical/Major/Minor] Finding #N**
> - 位置：`<file:line>`
> - 问题：<Codex 描述>
> - 建议：<Codex 建议>
> - 我的判断：<主 AI 是否同意及理由>

选项：
- `同意，立即修`
- `同意但晚点修（记入 bigmemory/热区/未关闭决策.md）`
- `部分采纳，我来说怎么改`
- `反驳 Codex 这条，跳过`
- `需要更多讨论`

严禁"批量接受所有 Codex 建议"——违反硬规则 #17（批判性思维）+ #22（human-in-the-loop）。

## 第七步：生成审查总结

所有 finding 处理完后，产出：

```
审查总结
- 审查范围：<scope + base>
- Codex 发现：X critical / Y major / Z minor
- Dr Sun 决定：A 立即修 / B 延后 / C 部分采纳 / D 反驳
- 后续动作：<列出立即修的清单>
```

若有"立即修"项，询问 Dr Sun 是否当场动手；若 Dr Sun 同意，按顺序修改并每修完一项 commit 一次。

## 何时不适用此命令

- **纯代码 review（不涉及论文/实验台账/文档）**：仍可用本命令，但 focus 选 "代码正确性与安全" 即可；若要用 Codex 的 `review`（非 adversarial）子命令以走 `validateNativeReviewRequest` 更严格校验，单独加 `/codex-review` 别名命令。
- **审主 AI 的规划/决策过程（不涉及文件改动）**：走 `/codex:adversarial-review` 直接对话或 `/delegate`，而非本命令。
- **审已 push 的远端 commit**：先 `git fetch`，然后 `--scope branch --base origin/main`。

## 稳定性要点

1. **禁用 `mcp__codex__*`**（60s 超时，审查必超）——本命令走 companion 直连，规避。
2. **nested session 冲突**：companion 在主 session 外起独立 Codex session，不嵌套。若报 `~/.codex/sessions` 权限冲突，`ps aux | grep codex` 查僵尸进程，kill 后重试。
3. **超大 diff**：若 `git diff --stat` 显示 >50 文件或 >5000 行，先 AskUserQuestion 让 Dr Sun 选"分批审 / 指定子目录 `--cwd`"，避免 Codex 上下文溢出。
4. **审查日志留档**：产出写入 `.pipeline/reviews/YYYYMMDD_<topic>.md`（新建目录），便于后续 `/archive` 汇总。
