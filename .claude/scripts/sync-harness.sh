#!/usr/bin/env bash
# Harness 完整性检查
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

FAIL=0

echo "== 1. CLAUDE.md → @AGENTS.md → AGENTS.md =="
# AGENTS.md 是真源,CLAUDE.md 仅为 Claude Code 入口 thin wrapper(硬规则 #15)
if [ ! -f "CLAUDE.md" ] || [ ! -f "AGENTS.md" ]; then
    echo "  ❌ 缺少 CLAUDE.md 或 AGENTS.md" >&2
    FAIL=1
elif [ ! -s "AGENTS.md" ]; then
    echo "  ❌ AGENTS.md 为空(应为内容真源)" >&2
    FAIL=1
elif ! grep -q '^@AGENTS\.md$' "CLAUDE.md"; then
    echo "  ❌ CLAUDE.md 缺少独立行 \`@AGENTS.md\` 引用(应为 thin wrapper)" >&2
    FAIL=1
else
    echo "  ✅ CLAUDE.md → @AGENTS.md → AGENTS.md"
fi

echo "== 2. 核心目录结构 =="
for dir in bigmemory/热区 bigmemory/冷区 .pipeline .claude/agents .claude/commands .claude/rules .claude/scripts .claude/skills .codex .codex/agents .codex/hooks .codex/rules .agents/skills; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ 不存在" >&2
        FAIL=1
    fi
done

echo "== 3. skills 目录非空 =="
if [ -d ".claude/skills" ]; then
    SKILL_COUNT=$(find .claude/skills -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$SKILL_COUNT" -gt 0 ]; then
        echo "  ✅ .claude/skills/ 包含 $SKILL_COUNT 个 skill"
    else
        echo "  ❌ .claude/skills/ 为空或无 SKILL.md" >&2
        FAIL=1
    fi
else
    echo "  ❌ .claude/skills/ 目录不存在" >&2
    FAIL=1
fi

if [ -d ".agents/skills" ]; then
    AGENT_SKILL_COUNT=$(find .agents/skills -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$AGENT_SKILL_COUNT" -gt 0 ]; then
        echo "  ✅ .agents/skills/ 包含 $AGENT_SKILL_COUNT 个 skill"
    else
        echo "  ❌ .agents/skills/ 为空或无 SKILL.md" >&2
        FAIL=1
    fi
else
    echo "  ❌ .agents/skills/ 目录不存在" >&2
    FAIL=1
fi

echo "== 4. 关键脚本 =="
for script in git-on-prompt.sh hot-zone-on-prompt.sh check-agents-sync.sh sync-harness.sh; do
    if [ -f ".claude/scripts/$script" ]; then
        echo "  ✅ $script"
    else
        echo "  ❌ $script 不存在" >&2
        FAIL=1
    fi
done

echo "== 4b. Codex 主入口配置 =="
if [ ! -s ".codex/config.toml" ]; then
    echo "  ❌ .codex/config.toml 不存在或为空" >&2
    FAIL=1
else
    CODEX_CHECK_OUTPUT=$(python3 - <<'PY' 2>&1
from pathlib import Path
import re
import sys

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

expected_agents = {
    "conductor.toml": "conductor",
    "experiment-driver.toml": "experiment_driver",
    "harness-explorer.toml": "harness_explorer",
    "harness-reviewer.toml": "harness_reviewer",
    "literature-scout.toml": "literature_scout",
    "memory-retriever.toml": "memory_retriever",
    "paper-writer.toml": "paper_writer",
    "reviewer.toml": "reviewer",
}
expected_skills = {
    "codex-audit",
    "delegate-offline",
    "experiment-loop",
    "idea-routing",
    "literature-survey",
    "paper-review",
    "paper-write",
    "project-setup",
    "project-status",
    "project-sync",
    "remote-ssh",
}

def fail(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)

config_path = Path(".codex/config.toml")
config_text = config_path.read_text()

if tomllib is not None:
    with config_path.open("rb") as f:
        config = tomllib.load(f)
    if not config.get("features", {}).get("codex_hooks", False):
        fail("Codex hooks feature is not enabled")
    author = (
        config.get("shell_environment_policy", {})
        .get("set", {})
        .get("GIT_AUTHOR_NAME")
    )
    if author == "Claude Code":
        fail("Codex config still uses Claude Code git author")

    for filename, expected_name in expected_agents.items():
        agent_path = Path(".codex/agents") / filename
        if not agent_path.is_file():
            fail(f"missing {agent_path}")
        with agent_path.open("rb") as f:
            agent = tomllib.load(f)
        for key in ("name", "description", "developer_instructions"):
            if not agent.get(key):
                fail(f"{agent_path} missing required field: {key}")
        if agent["name"] != expected_name:
            fail(f"{agent_path} name mismatch: {agent['name']} != {expected_name}")
else:
    if 'GIT_AUTHOR_NAME = "Claude Code"' in config_text:
        fail("Codex config still uses Claude Code git author")
    if 'codex_hooks = true' not in config_text:
        fail("Codex hooks feature is not enabled")
    for filename, expected_name in expected_agents.items():
        agent_path = Path(".codex/agents") / filename
        if not agent_path.is_file():
            fail(f"missing {agent_path}")
        text = agent_path.read_text()
        checks = [
            rf'^name\s*=\s*"{re.escape(expected_name)}"',
            r'^description\s*=',
            r'^developer_instructions\s*=',
        ]
        for pattern in checks:
            if not re.search(pattern, text, re.MULTILINE):
                fail(f"{agent_path} failed text check: {pattern}")

hooks_path = Path(".codex/hooks.json")
if not hooks_path.is_file():
    fail("missing .codex/hooks.json")
try:
    import json
    hooks = json.loads(hooks_path.read_text())
except Exception as exc:
    fail(f".codex/hooks.json is not valid JSON: {exc}")
for event in ("UserPromptSubmit", "PreToolUse", "PostToolUse"):
    if event not in hooks.get("hooks", {}):
        fail(f".codex/hooks.json missing event: {event}")

rules_path = Path(".codex/rules/harness.rules")
if not rules_path.is_file():
    fail("missing .codex/rules/harness.rules")

for skill in expected_skills:
    skill_path = Path(".agents/skills") / skill / "SKILL.md"
    if not skill_path.is_file():
        fail(f"missing {skill_path}")
PY
)
    CODEX_CHECK_STATUS=$?
    if [ "$CODEX_CHECK_STATUS" -ne 0 ]; then
        echo "  ❌ Codex 配置检查失败: $CODEX_CHECK_OUTPUT" >&2
        FAIL=1
    else
        echo "  ✅ .codex/config.toml"
    fi
fi

if [ -f ".codex/README.md" ]; then
    echo "  ✅ .codex/README.md"
else
    echo "  ❌ .codex/README.md 不存在" >&2
    FAIL=1
fi

echo "  ✅ .codex/agents/ academic harness agents"
echo "  ✅ .codex/hooks.json + .codex/rules/harness.rules"
echo "  ✅ .agents/skills/ project command skills"

echo "== 5. .pipeline 知识库完整性 =="
for f in .pipeline/README.md .pipeline/terminology/terminology.md .pipeline/literature/README.md .pipeline/literature/index.md .pipeline/survey/README.md .pipeline/experiments/README.md .pipeline/codex_tasks/README.md; do
    if [ -f "$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ $f 不存在" >&2
        FAIL=1
    fi
done

echo "== 6. bigmemory 热区文件 =="
for f in bigmemory/热区/状态简报.md bigmemory/热区/未关闭决策.md bigmemory/热区/近期改动.md bigmemory/格式规范.md; do
    if [ -f "$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ $f 不存在" >&2
        FAIL=1
    fi
done

echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "🟢 Harness 检查全部通过"
    exit 0
else
    echo "🔴 Harness 检查有失败项" >&2
    exit 2
fi
