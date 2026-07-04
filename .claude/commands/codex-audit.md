---
description: Ask Codex to peer-review all changes made by the main AI (Claude), covering code, paper, experiments, and documentation.
---

> **Use the AskUserQuestion tool for every confirmation step. Do not replace it with plain text.**

You are the Lite3 quadruped navigation DRL Conductor. This command makes **Codex reliably review every change made by the main AI (Claude)**, including but not limited to code, paper text, experiment ledgers, pipeline documents, and bigmemory. Use the companion `adversarial-review` channel through app-server JSON-RPC, not the MCP path with a 60s timeout.

## Step 1: Automatically Collect Review Scope

Run these Bash commands in parallel to inspect repository state:

```bash
git status --porcelain
git log --oneline -10
git diff --stat HEAD~1..HEAD
git diff --stat
```

Decision guide:
- Uncommitted changes exist -> recommend `working-tree` by default.
- No uncommitted changes, but the latest 1-3 commits look like main-AI work (for example commit messages contain `auto-backup before edit`) -> recommend `branch --base HEAD~N`.
- Feature branch exists and diverges from main -> recommend `branch --base main`.

## Step 2: Confirm Review Scope With AskUserQuestion

Show the automatically collected change summary, including changed files and affected directories, then offer:

- `Review uncommitted changes (--scope working-tree)`
- `Review latest commit (--scope branch --base HEAD~1)`
- `Review latest N commits (Dr Sun specifies N)`
- `Review current branch vs main (--scope branch --base main)`
- `Review custom base (Dr Sun provides ref)`
- `Cancel`

## Step 3: Confirm Review Focus With AskUserQuestion

```text
Options:
- Comprehensive review (no focus; let Codex decide)
- Code correctness and safety (bugs / boundaries / performance / risk)
- Paper writing quality and data consistency (check 3_paper/main.tex vs .pipeline/experiments/)
- Experiment design and Contract consistency (check experiment records vs .pipeline/contracts/)
- Terminology consistency (check against .pipeline/terminology/terminology.md)
- Custom focus (Dr Sun provides text)
```

If a specific focus is selected, add contextual guidance when composing the focus text. Example: terminology review focus should say `Check terminology compliance against .pipeline/terminology/terminology.md`.

## Step 4: Call codex-companion.mjs adversarial-review

Run with the Bash tool (`run_in_background=true`) so the main session is not blocked:

```bash
node "/Users/sun/.claude/plugins/cache/openai-codex/codex/1.0.2/scripts/codex-companion.mjs" \
  adversarial-review \
  --wait \
  --scope <working-tree|branch> \
  [--base <ref>] \
  [--model <model>] \
  "<focus text>"
```

Notes:
- `--wait` waits for the result; internally companion still uses app-server JSON-RPC, not a 60s-limited MCP path.
- Valid `--scope` values: `auto | working-tree | branch`.
- `--base` only applies under `--scope branch`.
- The focus text is a positional argument; do not add a `--focus` flag.
- For comprehensive review, leave focus text empty.

Use Monitor or periodic Read to poll output, then continue. If there is no output for 5 minutes, stop the background task and retry with `--scope auto` or a smaller scope.

## Step 5: Parse Codex Findings

Extract findings from Codex output and classify by severity:
- **Critical**: must fix, such as data errors, security issues, paper claims conflicting with Contract, or bugs.
- **Major**: strongly recommended fixes, such as experiment-ledger/paper data mismatch, terminology violations, or logic defects.
- **Minor**: improvements, such as wording, structure, or missing comments.

If Codex returns prose instead of a finding list, the main AI should split it into items.

## Step 6: Discuss Findings With Dr Sun One by One

Process findings from highest to lowest severity. For each finding, use `AskUserQuestion`:

> **[Critical/Major/Minor] Finding #N**
> - Location: `<file:line>`
> - Issue: <Codex description>
> - Suggestion: <Codex suggestion>
> - My judgment: <whether the main AI agrees and why>

Options:
- `Agree, fix now`
- `Agree, fix later (record in bigmemory/热区/未关闭决策.md)`
- `Partly accept; I will specify how`
- `Reject this Codex finding, skip`
- `Needs more discussion`

Never batch-accept all Codex suggestions. That violates critical-thinking and human-in-the-loop discipline.

## Step 7: Produce Review Summary

After all findings are handled, output:

```text
Review summary
- Review scope: <scope + base>
- Codex findings: X critical / Y major / Z minor
- Dr Sun decisions: A fix now / B defer / C partial accept / D reject
- Follow-up actions: <list immediate fixes>
```

If any item is marked `fix now`, ask Dr Sun whether to make the changes immediately. If Dr Sun agrees, fix them in order and commit after each item.

## When Not To Use This Command

- **Pure code review only, with no paper/experiment ledger/document involvement**: this command is still usable with focus `Code correctness and safety`. If you need Codex `review` rather than `adversarial-review` to go through stricter `validateNativeReviewRequest`, add a separate `/codex-review` alias command.
- **Reviewing the main AI's planning or decision process without file changes**: use `/codex:adversarial-review` direct dialogue or `/delegate`, not this command.
- **Reviewing already-pushed remote commits**: run `git fetch`, then use `--scope branch --base origin/main`.

## Stability Notes

1. **Disable `mcp__codex__*`**: it times out after 60s and is unsuitable for reviews. This command uses companion direct connection instead.
2. **Nested-session conflict**: companion starts an independent Codex session outside the main session. If `~/.codex/sessions` permission conflicts occur, check stale processes with `ps aux | grep codex`, kill them, and retry.
3. **Huge diffs**: if `git diff --stat` shows more than 50 files or more than 5000 lines, ask Dr Sun whether to review in batches or specify a subdirectory `--cwd`, to avoid Codex context overflow.
4. **Archive review logs**: write outputs to `.pipeline/reviews/YYYYMMDD_<topic>.md` (create the directory if needed), so later `/archive` can summarize them.
