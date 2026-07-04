---
name: gemini-do
description: 将任务委派给 Gemini CLI 执行
version: "1.0"
user-invocable: true
---

# Gemini 任务委派

将指定任务委派给 Google Gemini CLI 执行。适用于需要第二个 AI 视角、大上下文分析、或利用 Gemini 特长的场景。

## 模型配置

```
GEMINI_MODEL=gemini-3.1-pro-preview   # 最强可用（429 时降级 2.5-pro → Flash）
```

## 适用场景

- 大文件/大 diff 分析（利用 1M context window）
- 需要与 Codex 不同的视角
- 文献摘要、架构评审、策略建议
- 免费额度内的批量任务

## 执行步骤

### 1. 解析任务

用户会说类似：
- "让 Gemini 分析一下这个文件"
- "用 Gemini 做 XXX"
- "/gemini-do 总结 PLAN.md 的下一步建议"

从 `$ARGUMENTS` 提取具体任务。

### 2. 准备上下文

根据任务需要，收集相关文件内容：

```bash
# 如果涉及特定文件
cat <file> | gemini -m gemini-3.1-pro-preview -p "<任务描述>" 2>&1

# 如果涉及项目全局
(echo "项目结构："; find 2_experiment/nav_baselines 2_experiment/source_references -maxdepth 3 -type d; echo "---"; cat README.md docs/README.md) \
| gemini -m gemini-3.1-pro-preview -p "<任务描述>" 2>&1

# 如果是纯问答
gemini -m gemini-3.1-pro-preview -p "<问题>" 2>&1
```

### 3. 降级策略

429 时降级为默认模型：
```bash
gemini -p "<任务描述>" 2>&1
```

### 4. 展示结果

将 Gemini 的输出展示给 Dr Sun，标注"以下来自 Gemini (模型名)"。

## 与 codex-dispatch 的区别

| 维度 | gemini-do | codex-dispatch |
|------|-----------|----------------|
| 模型 | Gemini 2.5 Pro | GPT-5.4 |
| 上下文 | 需通过 pipe 传入 | 自动读项目文件 |
| 文件操作 | 不直接改文件 | 可改文件（有沙箱） |
| 成本 | 免费额度内零成本 | 消耗 OpenAI token |
| 擅长 | 大上下文、总结、评审 | 代码生成、调试、精确修改 |

## 注意

- Gemini 不会自动读项目文件，必须显式传入
- 超时设 120 秒，大任务可调至 300 秒
- 输出直接是纯文本，无需额外解析
