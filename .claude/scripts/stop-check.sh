#!/usr/bin/env bash
# Stop hook: 强制热区更新
# exit 0 = 放行, exit 2 = block（继续对话）
# 检查 bigmemory/热区/状态简报.md 的 mtime

STATUS="bigmemory/热区/状态简报.md"
MAX_AGE=300  # 秒

# 从 stdin 读取 JSON
INPUT=$(cat)

# 解析 stop_hook_active（优先 jq，降级 python3）
if command -v jq &>/dev/null; then
  ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
else
  ACTIVE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get('stop_hook_active',False)).lower())" 2>/dev/null || echo "false")
fi

# 防无限循环
if [ "$ACTIVE" = "true" ]; then
  exit 0
fi

# 检查热区状态简报是否存在
if [ ! -f "$STATUS" ]; then
  echo "❌ bigmemory/热区/状态简报.md 不存在。请先更新热区再结束。" >&2
  exit 2
fi

# 检查 mtime
if [[ "$(uname)" == "Darwin" ]]; then
  MTIME=$(stat -f %m "$STATUS")
else
  MTIME=$(stat -c %Y "$STATUS")
fi
NOW=$(date +%s)
AGE=$((NOW - MTIME))

if [ "$AGE" -gt "$MAX_AGE" ]; then
  echo "❌ 热区状态简报超过 ${MAX_AGE} 秒未更新。请更新 bigmemory/热区/状态简报.md 再结束。" >&2
  exit 2
fi

exit 0
