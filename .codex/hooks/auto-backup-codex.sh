#!/usr/bin/env bash
# ============================================================================
# Codex PreToolUse hook: create an automatic git backup before edits
# ----------------------------------------------------------------------------
# Codex parses hook stdout. If ordinary git commit text is written to stdout,
# Codex may treat it as hook JSON and fail parsing. This script therefore sends
# diagnostics to stderr only.
# Rules:
#   1. If nothing is staged, back up tracked and untracked files.
#   2. If something is already staged, add only tracked modifications so new
#      files are not mixed into manual staging.
#   3. If backup fails, fail open and write the reason to stderr so the hook
#      does not block Codex edits.
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
