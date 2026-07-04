---
name: agy-cli-workflow
description: Use when the user asks to call Antigravity, AGY, agy, or "反重力" CLI for a bounded external-agent task, review, rewrite, second opinion, or context analysis.
---

# AGY CLI Workflow

Use this skill to call Antigravity CLI (`agy`) as an external helper. AGY can draft, review, rewrite, summarize, or analyze bounded context. Codex still owns the final answer, verification, and file edits unless the user explicitly asks AGY to edit.

## Commands

One-shot task:

```bash
agy --print --print-timeout 2m <<'AGY_INPUT'
<TASK>
<CONTEXT>
AGY_INPUT
```

Interactive session only when requested:

```bash
agy --prompt-interactive "<TASK>"
```

Continue most recent AGY session:

```bash
agy --continue
```

Add extra workspace roots when needed:

```bash
agy --add-dir <path> --print --print-timeout 2m <<'AGY_INPUT'
<TASK>
AGY_INPUT
```

Use `--sandbox` when AGY should be restricted from terminal side effects. Avoid `--dangerously-skip-permissions` unless the user explicitly asks for AGY-owned edits and accepts the scope.

## Task Prompt Template

```text
Task: <specific job for AGY>
Context: <bounded file excerpts, command output, or question>
Output format: <exact expected format>
Rules:
- Preserve facts, file paths, numbers, code identifiers, and citations.
- Do not invent evidence.
- Do not edit files unless explicitly instructed.
- Say "UNKNOWN" for anything not supported by the provided context.
```

## Workflow

1. Convert the user request into a bounded AGY task: what to inspect, what context is allowed, and what output format is needed.
2. Pass only the needed context through stdin or `--add-dir`. Exclude secrets, credentials, and unrelated project state.
3. Run `agy --print --print-timeout 2m` for one-shot work. Use interactive mode or `--continue` only when the user asked for an AGY session.
4. Treat AGY output as a draft or second opinion. Verify claims against local files, tests, docs, or opened sources before using them.
5. If AGY suggests edits, Codex applies only the verified parts unless the user explicitly requested AGY-owned file edits.
6. After file edits, run task-appropriate verification and commit if project rules require it.

## Failure Handling

- `429` or capacity error: retry once after a short wait; if it fails again, continue locally and state that AGY was unavailable.
- Timeout or no output: stop AGY if needed and continue locally.
- AGY changes facts, hallucinates files, or ignores the prompt: discard that part.
- AGY writes outside the intended workspace: stop and inspect before continuing.

## Good Uses

- Plain-language rewrite, but not limited to it.
- Second opinion on a plan, design, or code review.
- Summarizing bounded files or command output.
- Checking whether an explanation sounds understandable.
- Asking for alternative wording or a concise task breakdown.

## Boundaries

- AGY output is not evidence.
- AGY does not make final research, experiment, training, or commit decisions.
- AGY should not receive private keys, tokens, credentials, or unnecessary data.
- AGY should not run long training, downloads, or destructive commands from this workflow.
