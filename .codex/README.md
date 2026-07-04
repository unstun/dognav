# Codex 主入口适配

本目录是 Codex CLI / Codex App 的项目级 harness 入口。`AGENTS.md` 是跨 CLI 规则真源。

## 当前仓库边界

- project root: `/Users/sun/tongbu/study/phdproject/machine-dog-nav`
- project topic: Lite3 quadruped navigation DRL
- source of truth: local repo
- walking base repo: `/Users/sun/tongbu/study/phdproject/machine-dog`

## 项目级配置

`.codex/config.toml` 只放项目共享配置：

- `project_doc_max_bytes = 65536`
- hooks enabled
- subagent/thread depth 上限
- Codex git author

模型、MCP、plugins、sandbox、approval 默认留给用户级配置或启动参数管理。

## Hooks

`.codex/hooks.json` 继承本项目可用 hook：

- `UserPromptSubmit`: 注入 git 状态、热区新鲜度；若 `.trellis/` 不存在，Trellis breadcrumb hook 静默退出。
- `PreToolUse`: 文件修改前做 git auto-backup。
- `PostToolUse`: 修改受信任知识库 Markdown 后，将 `reviewed: true` 重置为 `reviewed: false`。

## Skills

Codex skills 入口为 `.agents/skills/`。这些 skills 从 walking 基础仓库迁移而来，后续使用前必须检查是否仍含旧实验路径或旧证据 claim。

## 验证建议

```bash
git status --short
bash .claude/scripts/sync-harness.sh --check
python3 -m json.tool .codex/hooks.json >/dev/null
```
