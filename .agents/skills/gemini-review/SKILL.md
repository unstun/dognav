---
name: gemini-review
description: 让 Gemini (2.5 Pro) 审核 Codex 的所有改动和推理
version: "1.0"
user-invocable: true
---
# Gemini 审核

用 Google Gemini CLI 对 Codex 的改动做独立审核。审核范围不限于代码——涵盖改动理由、设计决策、文档变更等一切产出。

## 模型配置

```
GEMINI_MODEL=gemini-3.1-pro-preview   # 最强可用模型（429 时降级为 gemini-2.5-pro）
```

## 执行步骤

### 1. 收集审核上下文

同 codex-review：

```bash
git diff HEAD          # 未提交改动
git diff HEAD~1        # 或最近 commit
git diff HEAD --name-only
```

### 2. 构建审核 prompt 并调用 Gemini

将 diff + Codex 的改动理由通过管道传给 Gemini：

```bash
(echo "你是独立代码审查员，正在审核另一个 AI (Codex) 的改动。"; \
 echo ""; \
 echo "== 改动的文件 =="; \
 git diff HEAD --name-only; \
 echo ""; \
 echo "== 完整 diff =="; \
 git diff HEAD; \
 echo ""; \
 echo "== Codex 的改动理由 =="; \
 echo "{从会话上下文提取的理由}"; \
 echo ""; \
 echo "请从以下维度审核："; \
 echo "1. 逻辑正确性 2. 一致性 3. 遗漏 4. 风险 5. 理由是否站得住脚这五个维度只是建议不可以不被这个规则框死，终极目的就是检查 cladue 改的有没有问题"; \
 echo "按严重程度列出发现，附文件和行号。用中文回复。") \
| gemini -m gemini-3.1-pro-preview -p "审核以上 AI 改动" 2>&1
```

### 3. 降级策略

如果 `gemini-3.1-pro-preview` 返回 429 (RESOURCE_EXHAUSTED)，自动降级：

```bash
# 降级到 2.5 Pro
(...same pipe...) | gemini -m gemini-2.5-pro -p "审核以上 AI 改动" 2>&1
# 再 429 则降级到默认 Flash
(...same pipe...) | gemini -p "审核以上 AI 改动" 2>&1
```

### 4. 提取并展示结果

Gemini 的输出通常是纯文本，直接展示给 Dr Sun。

### 5. 可选：根据审核意见行动

如果 Gemini 发现了真实问题，询问 Dr Sun 是否需要修复。

## 与 Codex 审核的差异

| 维度       | Gemini                     | Codex                    |
| ---------- | -------------------------- | ------------------------ |
| 视角       | 研究顾问风格，关注上游决策 | 代码审查风格，精确到行号 |
| 上下文窗口 | 1M token，大 diff 无压力   | 受限，但会主动读文件验证 |
| 成本       | 免费额度内零成本           | 消耗 OpenAI token        |
| 速度       | 较快                       | 较慢（有推理链）         |

## 注意

- Gemini 不会自动读项目文件，所有上下文必须通过 pipe 传入
- 大 diff 是 Gemini 的优势（1M context window）
- 超时设 120 秒
