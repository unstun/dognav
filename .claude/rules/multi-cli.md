---
paths: [".pipeline/survey/multi-ai-workflow.md", "**/*codex*", "**/*gemini*", "**/*rescue*", "**/*delegate*"]
---
# 多 CLI 协作

主会话统筹者按当前 CLI 入口确定。Claude Code/Droid 主会话中, Codex 可通过官方插件 `openai/codex-plugin-cc` 接入（指令 `/codex:rescue`、子 agent `codex:codex-rescue`），走 app-server JSON-RPC 协议，自动继承 AGENTS.md。**Cursor 例外**：Codex 一律由主会话生成手动任务包，Dr Sun paste 到 Codex App（或在本机终端执行命令），主会话只审核回贴结果。**Codex 主入口**：Codex 直接读取 `AGENTS.md` 和 trusted `.codex/` 层，复杂 harness 核查优先 spawn `harness_explorer` + `harness_reviewer` 并行；两个 custom agents 默认 `sandbox_mode = "read-only"`，实际权限仍受父会话运行配置约束。
审查用 `/codex:review` 或 `/codex:adversarial-review`（Codex 侧）、`gemini-review`（Gemini 侧）、`dual-review`（两者并行交叉）。
任务外派：Claude Code/Droid 可用 `/delegate`（B 模式：spawn `codex:codex-rescue` 子 agent 后台执行）或 `/delegate-offline`（A 模式：生成 prompt 供独立终端运行 `codex` CLI）；**Cursor 默认只用 A 模式**。
详见 `.pipeline/survey/multi-ai-workflow.md`。
