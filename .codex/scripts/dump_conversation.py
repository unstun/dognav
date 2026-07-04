#!/usr/bin/env python3
"""
.codex/scripts/dump_conversation.py

Codex App 侧入口 wrapper —— 转发到主脚本 .claude/scripts/dump_conversation.py。
默认强制 source=codex，避免 auto 误选其他平台；用户可显式指定 --source 覆盖。
"""

import os
import sys
from pathlib import Path

# ------------------------------------------------------------------ #
#  转发逻辑
# ------------------------------------------------------------------ #

PROJ_ROOT = Path(__file__).resolve().parents[2]
MAIN_SCRIPT = PROJ_ROOT / ".claude" / "scripts" / "dump_conversation.py"

if not MAIN_SCRIPT.exists():
    sys.exit(f"[错误] 未找到主脚本: {MAIN_SCRIPT}")

args = sys.argv[1:]
if not any(a.startswith("--source") or a == "-s" for a in args):
    args = ["--source", "codex"] + args

os.execvp(sys.executable, [sys.executable, str(MAIN_SCRIPT)] + args)
