# 踩坑集合

## AI 使用踩坑

- WebFetch 与 WebSearch 不混在同一批并行调用(WebFetch 403 会级联拖垮同批 WebSearch),每批并行最多 2 个同类调用。
- PDF 链接大概率解析失败,优先 HTML 版本(如 `arxiv.org/html/`)。
- 子 agent 调用 prompt 必须强制其 WebFetch/Grep 真实源再答并附 URL + 原文片段。LLM 仍会伪造"原文引号"(quote-fabrication 已知失败模式),主会话必须 spot-check 引号字段。

## Context 管理踩坑

- 长篇论文 PDF 直接喂入会稀释 context 注意力，优先使用 arXiv LaTeX 源文件或 HTML 版本，按需只读相关 section。
- 安装报错、下载日志、训练 log 等高噪声内容一旦进入主 session context，后续所有推理质量都会下降。走 sub-agent 隔离。
- 多个 idea 混在同一 context 中讨论会互相干扰，AI 会不自觉地往之前的思路上靠。

## 多模型协作踩坑

- 让两个模型互相 review，永远能找到"还能改进的地方"。没有终局条件的互审循环是伪需求。必须有一个角色做最终决定。
- AI 会在实验结果出来后"合理化"任何数字——"虽然主指标没达标，但从另一个角度看..."。Research Contract 是唯一对策。
- Codex **在 Claude Code/Droid** 走 slash 命令（`/codex:review` `/codex:rescue` `/codex:adversarial-review`）或 Agent（`codex:codex-rescue`），**禁用** `mcp__codex__*`（已从 `~/Library/Application Support/Claude/claude_desktop_config.json` 删除）。**Cursor 例外**：不走 Codex 插件/Task，主 session 只生成手动任务包让 Dr Sun 输入 Codex。Why: TypeScript MCP SDK 硬编码 60s 请求超时；Cursor 插件路径又会消耗主会话调度 token 且 sandbox 与主 shell 不一致。
