#!/usr/bin/env python3
"""
dump_conversation.py — 手工导出 Claude Code / Droid / Cursor / Codex 会话为统一 Markdown
用法: python dump_conversation.py --output PATH [--session-id UUID] [--source claude|droid|cursor|codex|auto]
注意: /archive 已停用完整聊天记录归档；本脚本必须显式传 --output,避免重新写入 bigmemory。
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ------------------------------------------------------------------ #
#  常量
# ------------------------------------------------------------------ #

PROJ_DIR = Path(__file__).resolve().parents[2]                # 项目根目录
BJ_TZ = timezone(timedelta(hours=8))                          # UTC+8

# ---- Claude Code: ~/.claude/projects/<project-hash>/<session>.jsonl ---- #
CLAUDE_PROJ = Path.home() / ".claude" / "projects"
CC_PROJ_HASH = "-" + str(PROJ_DIR).replace("/", "-").lstrip("-")
CC_SESS_DIR = CLAUDE_PROJ / CC_PROJ_HASH

# ---- Factory/Droid: ~/.factory/sessions/<project-hash>/<session>.jsonl ---- #
FACTORY_SESS = Path.home() / ".factory" / "sessions"
DROID_PROJ_HASH = "-" + str(PROJ_DIR).replace("/", "-").lstrip("-")
DROID_SESS_DIR = FACTORY_SESS / DROID_PROJ_HASH

# ---- Cursor: ~/.cursor/projects/<project-hash>/agent-transcripts/<uuid>/<uuid>.jsonl ---- #
# Cursor hash 算法和 Claude Code 不同：路径 / 替换为 -，但**不加**前导 -
CURSOR_PROJ = Path.home() / ".cursor" / "projects"
CURSOR_PROJ_HASH = str(PROJ_DIR).replace("/", "-").lstrip("-")
CURSOR_SESS_DIR = CURSOR_PROJ / CURSOR_PROJ_HASH / "agent-transcripts"

# ---- Codex App: ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl ---- #
CODEX_SESS_DIR = Path.home() / ".codex" / "sessions"

# ---- JSONL 格式标识 ---- #
FORMAT_CLAUDE = "claude"
FORMAT_DROID = "droid"
FORMAT_CURSOR = "cursor"
FORMAT_CODEX = "codex"


# ------------------------------------------------------------------ #
#  格式检测
# ------------------------------------------------------------------ #

def detect_format(jsonl_path: Path) -> str:
    """读取第一行,自动判断 JSONL 格式。

    Claude Code: 第一行 type 为 "queue-operation" 或 "user",
                 消息行顶层 type 为 "user"/"assistant"。
    Droid:       第一行 type 为 "session_start",
                 消息行顶层 type 为 "message",role 在 message.role。
    Cursor:      顶层无 type 字段,仅有 role + message,
                 消息行顶层 role 为 "user"/"assistant"。
    """
    with open(jsonl_path) as f:
        first = json.loads(f.readline())
    if first.get("type") == "session_meta":
        return FORMAT_CODEX
    if first.get("type") == "session_start":
        return FORMAT_DROID
    if "type" not in first and "role" in first:
        return FORMAT_CURSOR
    return FORMAT_CLAUDE


# ------------------------------------------------------------------ #
#  会话发现
# ------------------------------------------------------------------ #

def find_latest_session(sess_dir: Path) -> Path | None:
    """找到目录下最新的 .jsonl 文件(按修改时间) — 用于扁平结构(Claude/Droid)"""
    if not sess_dir.exists():
        return None
    jsonls = sorted(sess_dir.glob("*.jsonl"), key=os.path.getmtime, reverse=True)
    return jsonls[0] if jsonls else None


def iter_cursor_sessions() -> list[Path]:
    """遍历 Cursor 所有 session 的 .jsonl 路径(两层结构: agent-transcripts/<uuid>/<uuid>.jsonl)"""
    if not CURSOR_SESS_DIR.exists():
        return []
    sessions = []
    for sess_dir in CURSOR_SESS_DIR.iterdir():
        if not sess_dir.is_dir():
            continue
        sessions.extend(sess_dir.glob("*.jsonl"))
    return sessions


def find_latest_cursor_session() -> Path | None:
    """找到 Cursor 最新的 session JSONL(按文件修改时间)"""
    sessions = iter_cursor_sessions()
    if not sessions:
        return None
    sessions.sort(key=os.path.getmtime, reverse=True)
    return sessions[0]


def _codex_session_matches_project(jsonl_path: Path) -> bool:
    """Codex session_meta 中 cwd 必须等于当前项目根目录。"""
    try:
        with open(jsonl_path) as f:
            first = json.loads(f.readline())
    except Exception:
        return False
    if first.get("type") != "session_meta":
        return False
    cwd = first.get("payload", {}).get("cwd")
    return Path(cwd).resolve() == PROJ_DIR if cwd else False


def iter_codex_sessions() -> list[Path]:
    """遍历 Codex App 当前项目的 rollout JSONL。"""
    if not CODEX_SESS_DIR.exists():
        return []
    return [
        p for p in CODEX_SESS_DIR.rglob("*.jsonl")
        if _codex_session_matches_project(p)
    ]


def find_latest_codex_session() -> Path | None:
    """找到 Codex App 当前项目最新的 session JSONL(按文件修改时间)。"""
    sessions = iter_codex_sessions()
    if not sessions:
        return None
    sessions.sort(key=os.path.getmtime, reverse=True)
    return sessions[0]


def find_codex_session_by_id(session_id: str) -> Path | None:
    """按 Codex session id 或 rollout 文件名查找当前项目 JSONL。"""
    for p in iter_codex_sessions():
        if p.stem == session_id or p.stem.endswith(session_id):
            return p
        try:
            with open(p) as f:
                first = json.loads(f.readline())
            if first.get("payload", {}).get("id") == session_id:
                return p
        except Exception:
            continue
    return None


def find_session_by_id(session_id: str, source: str) -> Path | None:
    """按 session_id 查找 JSONL 文件"""
    candidates = []
    if source in ("claude", "auto"):
        p = CC_SESS_DIR / f"{session_id}.jsonl"
        if p.exists():
            candidates.append(p)
    if source in ("droid", "auto"):
        p = DROID_SESS_DIR / f"{session_id}.jsonl"
        if p.exists():
            candidates.append(p)
    if source in ("cursor", "auto"):
        # Cursor 路径: agent-transcripts/<session_id>/<session_id>.jsonl
        p = CURSOR_SESS_DIR / session_id / f"{session_id}.jsonl"
        if p.exists():
            candidates.append(p)
    if source in ("codex", "auto"):
        p = find_codex_session_by_id(session_id)
        if p:
            candidates.append(p)
    return candidates[0] if candidates else None


def pick_latest(source: str) -> Path:
    """根据 source 参数选最新会话文件"""
    candidates = []
    if source in ("claude", "auto"):
        p = find_latest_session(CC_SESS_DIR)
        if p:
            candidates.append(p)
    if source in ("droid", "auto"):
        p = find_latest_session(DROID_SESS_DIR)
        if p:
            candidates.append(p)
    if source in ("cursor", "auto"):
        p = find_latest_cursor_session()
        if p:
            candidates.append(p)
    if source in ("codex", "auto"):
        p = find_latest_codex_session()
        if p:
            candidates.append(p)

    if not candidates:
        sys.exit(f"[错误] 未找到任何会话 (source={source})")

    # auto 模式取修改时间最新的
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


# ------------------------------------------------------------------ #
#  Claude Code subagent 发现
# ------------------------------------------------------------------ #

def find_cc_subagent_files(session_id: str) -> list[Path]:
    """找到 Claude Code 会话的所有 subagent JSONL"""
    sub_dir = CC_SESS_DIR / session_id / "subagents"
    if not sub_dir.exists():
        return []
    return sorted(sub_dir.glob("*.jsonl"), key=os.path.getmtime)


# ------------------------------------------------------------------ #
#  时间戳解析
# ------------------------------------------------------------------ #

def parse_timestamp(ts_str: str) -> datetime | None:
    """ISO 时间戳 → 北京时间,失败返回 None"""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.astimezone(BJ_TZ)
    except Exception:
        return None


# ------------------------------------------------------------------ #
#  内容提取(通用)
# ------------------------------------------------------------------ #

def extract_text(content) -> str:
    """从 message.content 中提取纯文本(跳过 thinking/tool_use/tool_result)"""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if block.get("type") == "text":
                parts.append(block["text"].strip())
        return "\n\n".join(parts)
    return ""


def compact_inline(text: str) -> str:
    """把工具参数压成单行,避免破坏会话记录版式。"""
    return re.sub(r"\s+", " ", text).strip()


def extract_tool_calls(content) -> list[str]:
    """提取 tool_use 摘要(工具名 + 简短参数)"""
    if not isinstance(content, list):
        return []
    calls = []
    for block in content:
        if block.get("type") == "tool_use":
            name = block.get("name", "?")
            inp = block.get("input", {})
            summary_parts = []
            for k, v in inp.items():
                raw = compact_inline(str(v))
                v_str = raw[:80]
                if len(raw) > 80:
                    v_str += "..."
                summary_parts.append(f"{k}={v_str}")
            summary = ", ".join(summary_parts[:3])
            if len(summary_parts) > 3:
                summary += ", ..."
            calls.append(f"`{name}({summary})`")
    return calls


def append_tool_turn(lines: list[str], tools: list[str], time_label: str = "") -> None:
    """按 Claude Code 会话导出的外形写入工具调用。"""
    if not tools:
        return
    lines.append(f"**AI** [{time_label}]:")
    lines.append("")
    lines.append("工具调用: " + " → ".join(tools[:5]))
    if len(tools) > 5:
        lines.append(f"  ... 共 {len(tools)} 个调用")
    lines.append("")


# ------------------------------------------------------------------ #
#  跳过判断(通用)
# ------------------------------------------------------------------ #

def should_skip_user_text(text: str) -> bool:
    """判断用户消息是否应跳过(系统注入的 meta 内容)"""
    if not text:
        return True
    prefixes = (
        "<system-reminder>",
        "<task-notification>",
        "<local-command",
        "<turn_aborted>",
        "<subagent_notification>",
        "<environment_context>",
        "<heartbeat>",
        "# AGENTS.md instructions",
    )
    return text.startswith(prefixes)


def clean_command_text(text: str) -> str:
    """提取 command 名称(如有)"""
    if "<command-name>" in text:
        m = re.search(r"<command-name>(.*?)</command-name>", text)
        if m:
            return f"/{m.group(1)}"
    return text


# ------------------------------------------------------------------ #
#  Droid 格式解析
# ------------------------------------------------------------------ #

def process_droid_jsonl(jsonl_path: Path, label: str = "主会话") -> list[str]:
    """解析 Factory/Droid 的 JSONL。

    格式特征:
    - session_start 行: type="session_start", 含 id/title/owner/cwd
    - 消息行: type="message", message.role="user"/"assistant"
    - todo 行: type="todo_state"(跳过)
    - 用户真实输入在 content 列表的最后一个 text block
    - system-reminder 在 content 列表的前面 text block
    """
    lines = [f"### {label}", ""]
    session_title = ""

    with open(jsonl_path) as f:
        for raw_line in f:
            obj = json.loads(raw_line)
            msg_type = obj.get("type")

            # 提取会话标题
            if msg_type == "session_start":
                session_title = (
                    obj.get("sessionTitle") or obj.get("title") or ""
                )
                continue

            if msg_type != "message":
                continue

            msg = obj.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", "")
            ts_str = obj.get("timestamp", "")
            dt = parse_timestamp(ts_str)
            time_label = dt.strftime("%H:%M") if dt else ""

            if role == "user":
                # content 是 list[block],真实用户输入是最后一个非 system 的 text block
                text = _extract_real_user_text_droid(content)
                if not text:
                    continue
                text = clean_command_text(text)
                lines.append(f"**Dr Sun** [{time_label}]:")
                lines.append(f"> {text}")
                lines.append("")

            elif role == "assistant":
                text = extract_text(content)
                tools = extract_tool_calls(content)
                if not text and not tools:
                    continue
                lines.append(f"**AI** [{time_label}]:")
                if text:
                    if len(text) > 2000:
                        text = text[:2000] + "\n\n... (截断,完整内容见原始 JSONL)"
                    lines.append(text)
                if tools:
                    lines.append("")
                    lines.append("工具调用: " + " → ".join(tools[:5]))
                    if len(tools) > 5:
                        lines.append(f"  ... 共 {len(tools)} 个调用")
                lines.append("")

    return lines, session_title


def _extract_real_user_text_droid(content) -> str:
    """从 Droid 用户消息的 content blocks 中提取真实用户输入。

    Droid 的 user message content 通常为:
    [text(system-reminder), text(system-reminder), ..., text(真实输入)]
    或 [tool_result] (工具返回,跳过)
    """
    if isinstance(content, str):
        if should_skip_user_text(content):
            return ""
        return content.strip()

    if not isinstance(content, list):
        return ""

    # 从后往前找第一个不是 system-reminder 的 text block
    for block in reversed(content):
        if block.get("type") != "text":
            continue
        text = block.get("text", "").strip()
        if not should_skip_user_text(text):
            return text

    return ""


# ------------------------------------------------------------------ #
#  Claude Code 格式解析
# ------------------------------------------------------------------ #

def process_claude_jsonl(jsonl_path: Path, label: str = "主会话") -> list[str]:
    """解析 Claude Code 的 JSONL。

    格式特征:
    - 消息行顶层 type 为 "user"/"assistant"
    - isMeta=true 的 user 消息跳过
    - content 可以是 str 或 list[block]
    """
    lines = [f"### {label}", ""]

    with open(jsonl_path) as f:
        for raw_line in f:
            obj = json.loads(raw_line)
            msg_type = obj.get("type")

            if msg_type not in ("user", "assistant"):
                continue

            msg = obj.get("message", {})
            content = msg.get("content", "")
            ts_str = obj.get("timestamp", "")
            dt = parse_timestamp(ts_str)
            time_label = dt.strftime("%H:%M") if dt else ""

            if msg_type == "user":
                # 跳过 meta 消息
                if obj.get("isMeta"):
                    continue
                text = extract_text(content)
                if should_skip_user_text(text):
                    continue
                text = clean_command_text(text)
                lines.append(f"**Dr Sun** [{time_label}]:")
                lines.append(f"> {text}")
                lines.append("")

            elif msg_type == "assistant":
                text = extract_text(content)
                tools = extract_tool_calls(content)
                if not text and not tools:
                    continue
                lines.append(f"**AI** [{time_label}]:")
                if text:
                    if len(text) > 2000:
                        text = text[:2000] + "\n\n... (截断,完整内容见原始 JSONL)"
                    lines.append(text)
                if tools:
                    lines.append("")
                    lines.append("工具调用: " + " → ".join(tools[:5]))
                    if len(tools) > 5:
                        lines.append(f"  ... 共 {len(tools)} 个调用")
                lines.append("")

    return lines, ""


# ------------------------------------------------------------------ #
#  Cursor 格式解析
# ------------------------------------------------------------------ #

TIMESTAMP_RE = re.compile(r"<timestamp>([^<]+)</timestamp>")
USER_QUERY_RE = re.compile(r"<user_query>\s*(.+?)\s*</user_query>", re.DOTALL)


def _parse_cursor_timestamp(content) -> datetime | None:
    """从 Cursor 用户消息里解析 <timestamp>...</timestamp> 标签。

    标签格式示例: "Monday, Apr 27, 2026, 2:05 AM (UTC-7)"
    """
    if not isinstance(content, list):
        return None
    for block in content:
        if block.get("type") != "text":
            continue
        m = TIMESTAMP_RE.search(block.get("text", ""))
        if not m:
            continue
        ts_str = m.group(1).strip()
        # 提取时区偏移,strptime 不接受 "UTC-7" 这种格式
        tz_match = re.search(r"\(UTC([+-]\d+)\)", ts_str)
        body = re.sub(r"\s*\(UTC[+-]\d+\)\s*$", "", ts_str)
        try:
            dt = datetime.strptime(body, "%A, %b %d, %Y, %I:%M %p")
            if tz_match:
                offset_h = int(tz_match.group(1))
                tz = timezone(timedelta(hours=offset_h))
                dt = dt.replace(tzinfo=tz)
            else:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(BJ_TZ)
        except Exception:
            return None
    return None


def _extract_real_user_text_cursor(content) -> str:
    """从 Cursor 用户消息提取真实用户输入。

    Cursor user message 可能形态:
    - 首条: 含大量 system context + <user_query>真实输入</user_query>
    - 后续: tool_result(跳过) 或纯 text
    """
    if isinstance(content, str):
        if should_skip_user_text(content):
            return ""
        return content.strip()

    if not isinstance(content, list):
        return ""

    # ------- 1. 优先找 <user_query> 标签内的真实输入 ------- #
    for block in content:
        if block.get("type") != "text":
            continue
        m = USER_QUERY_RE.search(block.get("text", ""))
        if m:
            return m.group(1).strip()

    # ------- 2. 跳过 tool_result,取第一个非 system 标记的 text block ------- #
    for block in content:
        btype = block.get("type")
        if btype == "tool_result":
            continue
        if btype == "text":
            text = block.get("text", "").strip()
            if text and not should_skip_user_text(text):
                return text

    return ""


def process_cursor_jsonl(jsonl_path: Path, label: str = "主会话") -> tuple[list[str], str]:
    """解析 Cursor 的 JSONL。

    格式特征:
    - 顶层 {role: "user"|"assistant", message: {content: list[block]}}
    - 无顶层 timestamp 字段(从 <timestamp> 标签解析,assistant 沿用最近的 user 时间)
    - user 首条含 <timestamp> + <user_query>; 后续可能是 tool_result(跳过)
    """
    lines = [f"### {label}", ""]
    last_dt = None

    with open(jsonl_path) as f:
        for raw_line in f:
            obj = json.loads(raw_line)
            role = obj.get("role", "")
            msg = obj.get("message", {})
            content = msg.get("content", "")

            if role == "user":
                # 更新时间戳锚点(若本条含 <timestamp>)
                dt = _parse_cursor_timestamp(content)
                if dt:
                    last_dt = dt
                time_label = last_dt.strftime("%H:%M") if last_dt else ""

                text = _extract_real_user_text_cursor(content)
                if not text:
                    continue
                text = clean_command_text(text)
                lines.append(f"**Dr Sun** [{time_label}]:")
                lines.append(f"> {text}")
                lines.append("")

            elif role == "assistant":
                time_label = last_dt.strftime("%H:%M") if last_dt else ""
                text = extract_text(content)
                tools = extract_tool_calls(content)
                if not text and not tools:
                    continue
                lines.append(f"**AI** [{time_label}]:")
                if text:
                    if len(text) > 2000:
                        text = text[:2000] + "\n\n... (截断,完整内容见原始 JSONL)"
                    lines.append(text)
                if tools:
                    lines.append("")
                    lines.append("工具调用: " + " → ".join(tools[:5]))
                    if len(tools) > 5:
                        lines.append(f"  ... 共 {len(tools)} 个调用")
                lines.append("")

    return lines, ""


# ------------------------------------------------------------------ #
#  Codex App 格式解析
# ------------------------------------------------------------------ #

def extract_codex_text(content) -> str:
    """从 Codex message content 中提取可读文本。"""
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    parts = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") in ("input_text", "output_text", "text"):
            text = block.get("text", "").strip()
            if text:
                parts.append(text)
    return "\n\n".join(parts)


def _shorten_tool_arguments(args) -> str:
    """把 Codex function_call arguments 压缩成单行摘要。"""
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
        except Exception:
            raw = compact_inline(args)
            return raw[:120] + ("..." if len(raw) > 120 else "")
    else:
        parsed = args

    if isinstance(parsed, dict):
        parts = []
        for k, v in parsed.items():
            v_str = compact_inline(str(v))
            if len(v_str) > 80:
                v_str = v_str[:80] + "..."
            parts.append(f"{k}={v_str}")
        return ", ".join(parts[:3]) + (", ..." if len(parts) > 3 else "")

    text = compact_inline(str(parsed))
    return text[:120] + ("..." if len(text) > 120 else "")


def process_codex_jsonl(jsonl_path: Path, label: str = "主会话") -> tuple[list[str], str]:
    """解析 Codex App 的 rollout JSONL。

    格式特征:
    - 首行 type=session_meta, payload 内含 id/cwd/originator/source/model
    - 对话消息为 type=response_item, payload.type=message
    - 用户文本块 type=input_text, AI 文本块 type=output_text
    - 工具调用为 payload.type=function_call / tool_search_call
    """
    lines = [f"### {label}", ""]
    title = ""
    pending_tools: list[str] = []
    pending_tool_time = ""

    def flush_tools():
        nonlocal pending_tools, pending_tool_time
        if not pending_tools:
            return
        append_tool_turn(lines, pending_tools, pending_tool_time)
        pending_tools = []
        pending_tool_time = ""

    with open(jsonl_path) as f:
        for raw_line in f:
            obj = json.loads(raw_line)
            ts_str = obj.get("timestamp", "")
            dt = parse_timestamp(ts_str)
            time_label = dt.strftime("%H:%M") if dt else ""

            if obj.get("type") == "session_meta":
                payload = obj.get("payload", {})
                title = payload.get("title") or payload.get("id") or ""
                continue

            if obj.get("type") != "response_item":
                continue

            payload = obj.get("payload", {})
            ptype = payload.get("type")

            if ptype in ("function_call", "tool_search_call", "custom_tool_call"):
                name = payload.get("name") or ptype
                args = (
                    payload.get("arguments")
                    or payload.get("input")
                    or payload.get("query")
                    or ""
                )
                pending_tools.append(f"`{name}({_shorten_tool_arguments(args)})`")
                pending_tool_time = time_label or pending_tool_time
                continue

            if ptype != "message":
                continue

            role = payload.get("role", "")
            if role not in ("user", "assistant"):
                continue

            text = extract_codex_text(payload.get("content", ""))
            if role == "user":
                if should_skip_user_text(text):
                    continue
                flush_tools()
                text = clean_command_text(text)
                lines.append(f"**Dr Sun** [{time_label}]:")
                lines.append(f"> {text}")
                lines.append("")

            elif role == "assistant":
                if not text:
                    continue
                flush_tools()
                lines.append(f"**AI** [{time_label}]:")
                if len(text) > 2000:
                    text = text[:2000] + "\n\n... (截断,完整内容见原始 JSONL)"
                lines.append(text)
                lines.append("")

    flush_tools()
    return lines, title


# ------------------------------------------------------------------ #
#  统一入口
# ------------------------------------------------------------------ #

def process_jsonl(jsonl_path: Path, label: str = "主会话") -> tuple[list[str], str]:
    """自动检测格式并解析,返回 (markdown行列表, 会话标题)"""
    fmt = detect_format(jsonl_path)
    if fmt == FORMAT_DROID:
        return process_droid_jsonl(jsonl_path, label)
    if fmt == FORMAT_CURSOR:
        return process_cursor_jsonl(jsonl_path, label)
    if fmt == FORMAT_CODEX:
        return process_codex_jsonl(jsonl_path, label)
    return process_claude_jsonl(jsonl_path, label)


def detect_platform_label(jsonl_path: Path) -> str:
    """返回平台标签用于输出元数据"""
    fmt = detect_format(jsonl_path)
    if fmt == FORMAT_DROID:
        # 从 settings.json 读取模型信息
        settings_path = jsonl_path.with_suffix(".settings.json")
        model = "?"
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    s = json.load(f)
                model = s.get("model", "?")
            except Exception:
                pass
        return f"Droid ({model})"
    if fmt == FORMAT_CURSOR:
        return "Cursor"
    if fmt == FORMAT_CODEX:
        return "Codex App"
    return "Claude Code"


# ------------------------------------------------------------------ #
#  主流程
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(
        description="导出 Claude Code / Droid / Cursor / Codex 会话为 Markdown"
    )
    parser.add_argument("--session-id", help="指定会话 UUID,默认取最新")
    parser.add_argument(
        "--source", "-s",
        choices=["claude", "droid", "cursor", "codex", "auto"],
        default="auto",
        help="选择平台: claude / droid / cursor / codex / auto(默认 auto,所有平台中取最新)",
    )
    parser.add_argument("--output", "-o", required=True, help="输出路径；不允许默认写入 bigmemory")
    args = parser.parse_args()

    # ---- 定位会话文件 ---- #
    if args.session_id:
        jsonl_path = find_session_by_id(args.session_id, args.source)
        if not jsonl_path:
            sys.exit(f"[错误] 找不到会话: {args.session_id} (source={args.source})")
    else:
        jsonl_path = pick_latest(args.source)

    session_id = jsonl_path.stem
    mod_time = datetime.fromtimestamp(jsonl_path.stat().st_mtime, tz=BJ_TZ)
    platform = detect_platform_label(jsonl_path)
    fmt = detect_format(jsonl_path)

    print(f"[信息] 平台: {platform}")
    print(f"[信息] 会话: {session_id}")
    print(f"[信息] 文件: {jsonl_path}")
    print(f"[信息] 大小: {jsonl_path.stat().st_size / 1024:.0f} KB")

    # ---- 解析主会话 ---- #
    md_lines = []
    content_lines, session_title = process_jsonl(jsonl_path, "主会话")

    md_lines.append("# 会话记录")
    md_lines.append(f"> 会话 ID: `{session_id}`")
    md_lines.append(f"> 平台: {platform}")
    if session_title:
        md_lines.append(f"> 标题: {session_title}")
    md_lines.append(f"> 导出时间: {mod_time.strftime('%Y-%m-%d %H:%M')}")
    md_lines.append("")
    md_lines.extend(content_lines)

    # ---- 解析 subagent(仅 Claude Code 有子目录结构) ---- #
    if fmt == FORMAT_CLAUDE:
        sub_files = find_cc_subagent_files(session_id)
        if sub_files:
            md_lines.append("---")
            md_lines.append("")
            md_lines.append("## Subagent 会话")
            md_lines.append("")
            for sf in sub_files:
                agent_name = sf.stem
                sub_lines, _ = process_jsonl(sf, f"Agent: {agent_name}")
                md_lines.extend(sub_lines)
                md_lines.append("---")
                md_lines.append("")

    # ---- 输出 ---- #
    output_text = "\n".join(md_lines)

    out_path = Path(args.output)

    out_path.write_text(output_text, encoding="utf-8")
    print(f"[完成] 已导出到 {out_path}")
    print(f"[信息] 共 {len(output_text)} 字符, {output_text.count(chr(10))} 行")


if __name__ == "__main__":
    main()
