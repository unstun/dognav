# Imported Harness Notes

`machine-dog-nav` 从 `machine-dog` 迁移了 `.codex/`、`.claude/` 和 `.agents/skills/` 的主要 harness 配置。

## 已清理

- 项目绝对路径已改为 `/Users/sun/tongbu/study/phdproject/machine-dog-nav`。
- 常用实验入口已改为 `2_experiment/nav_baselines/` 和 `2_experiment/source_references/`。
- 顶层 `AGENTS.md` 明确旧 walking 记录不能作为 nav 实验证据。

## 仍需注意

部分迁移 skill 的 reference/example 文件仍包含旧 walking 示例，例如 `wave_c_*`、`v9j*`、`ELMAP`。这些只作为模板示例或历史线索，不代表本仓库当前状态。

使用这类 skill 前必须先读：

1. `AGENTS.md`
2. `README.md`
3. `docs/walking_base_handoff.md`
4. 当前 `.pipeline/contracts/` 和 `.pipeline/experiments/`
