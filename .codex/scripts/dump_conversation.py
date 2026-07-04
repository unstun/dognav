#!/usr/bin/env python3
"""
.codex/scripts/dump_conversation.py

Codex App entry wrapper: forwards to the main script at
.claude/scripts/dump_conversation.py.
Forces source=codex by default to avoid auto-selecting another platform; users
may pass --source explicitly to override it.
"""

import os
import sys
from pathlib import Path

# ------------------------------------------------------------------ #
#  Forwarding logic
# ------------------------------------------------------------------ #

PROJ_ROOT = Path(__file__).resolve().parents[2]
MAIN_SCRIPT = PROJ_ROOT / ".claude" / "scripts" / "dump_conversation.py"

if not MAIN_SCRIPT.exists():
    sys.exit(f"[error] main script not found: {MAIN_SCRIPT}")

args = sys.argv[1:]
if not any(a.startswith("--source") or a == "-s" for a in args):
    args = ["--source", "codex"] + args

os.execvp(sys.executable, [sys.executable, str(MAIN_SCRIPT)] + args)
