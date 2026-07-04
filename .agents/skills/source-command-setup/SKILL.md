---
name: "source-command-setup"
description: "初始化研究 Harness 结构（bigmemory/ + .pipeline/ + .Codex/）"
---

# source-command-setup

Use this skill when the user asks to run the migrated source command `setup`.

## Command Template

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你正在为当前目录初始化 Lite3 机器狗导航 DRL 研究 Harness。

## 第一步：检查现有结构

```bash
ls -la bigmemory/ .pipeline/ .Codex/ 2>/dev/null || echo "部分目录不存在"
```

用 `AskUserQuestion` 告知状态：

> **环境检查**：
> - bigmemory/：[存在 / 不存在]
> - .pipeline/：[存在 / 不存在]
> - .Codex/：[存在 / 不存在]

选项：
- `初始化缺失的目录`
- `全部重新初始化（会覆盖现有文件）`
- `取消`

## 第二步：创建目录结构

```bash
# bigmemory — 会话记忆（热区/冷区）
mkdir -p bigmemory/热区
mkdir -p bigmemory/冷区/{改动记录,踩坑记录,调研记录,心路历程,里程碑}
touch bigmemory/冷区/{改动记录,踩坑记录,调研记录,心路历程,里程碑}/.gitkeep

# .pipeline — 项目知识库（平文件数据库）
mkdir -p .pipeline/{terminology,literature,survey,experiments}

# .Codex — Agent 配置
mkdir -p .Codex/{agents,commands,rules,scripts,skills}

```

## 第三步：写入初始文件（已存在则跳过）

**bigmemory/热区/状态简报.md**：
```markdown
# 项目状态简报
> 最后更新：[ISO 日期时间]

## 当前在做什么
- [待填写]

## 关键上下文
- 实验代码：按 nav baseline 子项目声明 Python module，默认目录 `2_experiment/nav_baselines/<topic>/`。
- 机器人：云深处 Lite3 四足机器狗 (12 DOF)
- 仿真：Isaac Lab / MuJoCo
- 算法：PPO / SAC（连续动作空间）
- 任务：机器狗导航（具体任务需由 Research Contract 定义）

## 近期警告
- （无）
```

**bigmemory/热区/未关闭决策.md** 和 **近期改动.md**：创建空白模板。

**bigmemory/格式规范.md**：从模板生成（热区容量预算 + 冷区格式）。

**.pipeline/README.md**：知识库说明。

**.pipeline/terminology/terminology.md**、**.pipeline/literature/index.md**、各库 **README.md**：创建空白初始版本。

## 第四步：验证 Harness 完整性

```bash
bash .Codex/scripts/sync-harness.sh
```

## 第五步：完成确认

用 `AskUserQuestion`：

> Harness 初始化完成！
>
> 结构：
> - `bigmemory/` — 会话记忆（热区 + 冷区）
> - `.pipeline/` — 项目知识库（术语/文献/综述/实验）
> - `.Codex/` — Agent 配置（agents/commands/rules/scripts/skills）
>
> 接下来：
> - 运行 `/plan` 查看整体状态
> - 或直接开始工作

选项：
- `开始！运行 /plan`
- `我先自己看看文件结构`
