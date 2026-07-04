#!/usr/bin/env bash
# ============================================================================
# 校验 CLAUDE.md 通过 @AGENTS.md 正确引用 AGENTS.md (硬规则 #15)
# ----------------------------------------------------------------------------
# 设计:AGENTS.md 是内容真源,CLAUDE.md 仅为 Claude Code 入口 thin wrapper。
# Claude Code 启动 / /compact 后会自动展开 @AGENTS.md import 注入 context。
# 官方文档: https://code.claude.com/docs/en/memory#agents-md
# ============================================================================
set -euo pipefail

A="CLAUDE.md"
B="AGENTS.md"

# ---- 1. 文件存在性 -------------------------------------------------------
if [ ! -f "$A" ] || [ ! -f "$B" ]; then
  echo "❌ 缺少 $A 或 $B" >&2
  exit 2
fi

# ---- 2. AGENTS.md 是真源,必须非空 ---------------------------------------
if [ ! -s "$B" ]; then
  echo "❌ $B 为空(应为内容真源)" >&2
  exit 2
fi

# ---- 3. CLAUDE.md 必须含且仅含一行独立的 @AGENTS.md 引用 -----------------
IMPORT_LINES=$(grep -c '^@AGENTS\.md$' "$A" || true)
if [ "$IMPORT_LINES" -ne 1 ]; then
  echo "❌ $A 应含且仅含一行独立的 \`@AGENTS.md\` 引用,实际匹配:$IMPORT_LINES" >&2
  echo "   修复: 在 $A 中放一行 '@AGENTS.md'(顶格,前后空行)" >&2
  exit 2
fi

# ---- 4. 通过 ------------------------------------------------------------
echo "✅ CLAUDE.md → @AGENTS.md → AGENTS.md 引用正确"
exit 0
