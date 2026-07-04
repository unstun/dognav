#!/usr/bin/env bash
# ============================================================================
# Codex PreToolUse hook: edit 前自动创建 git 备份
# ----------------------------------------------------------------------------
# Codex 会解析 hook stdout。git commit 的普通文本如果写入 stdout，会被
# 误认为 hook JSON 并导致解析失败。因此本脚本只允许诊断信息进入 stderr。
# 规则:
#   1. 无 staged 内容时,备份 tracked + untracked 文件。
#   2. 已有 staged 内容时,只补充 tracked 修改,避免把新文件混进人工 staging。
#   3. 备份失败时 fail open,把原因写入 stderr,避免 hook 卡住 Codex 编辑。
# ============================================================================
set -euo pipefail

cat >/dev/null || true

git_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$git_root"

if git diff --quiet && git diff --cached --quiet && \
  [[ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]]; then
  exit 0
fi

err_log="${TMPDIR:-/tmp}/codex-auto-backup.err"
: >"$err_log"

pre_staged="$(git diff --cached --name-only 2>/dev/null || true)"

if [[ -n "$pre_staged" ]]; then
  if ! git add -u -- . ":(exclude).pipeline/contracts/**" 2>>"$err_log"; then
    echo "auto-backup: git add -u failed; see $err_log" >&2
    exit 0
  fi
else
  if ! git add -A -- . ":(exclude).pipeline/contracts/**" 2>>"$err_log"; then
    echo "auto-backup: git add -A failed; see $err_log" >&2
    exit 0
  fi
fi

if git diff --cached --quiet; then
  exit 0
fi

if ! git commit -m "auto-backup before edit" >>"$err_log" 2>&1; then
  echo "auto-backup: git commit failed; see $err_log" >&2
  exit 0
fi

exit 0
