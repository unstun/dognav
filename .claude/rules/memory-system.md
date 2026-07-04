---
paths:
  - "bigmemory/**"
  - ".pipeline/**"
---
# Memory System Detailed Structure

## bigmemory/ (on-demand retrieval, transparent reads/writes)

- `热区/状态简报.md` - current project state (<=1500 Chinese characters)
- `热区/未关闭决策.md` - open research/technical decisions (<=1200 Chinese characters)
- `热区/近期改动.md` - recent 7-day change summary (<=1000 Chinese characters)
- `冷区/改动记录/` - daily archive: YYYY-MM-DD.md, append-only
- `冷区/踩坑记录/` - daily archive, append-only
- `冷区/调研记录/` - daily archive, append-only
- `冷区/心路历程/` - daily archive, append-only
- `冷区/里程碑/` - daily archive, append-only
- `冷区/偏好.md` - user preferences, single file
- `冷区/工作流.md` - standard workflow, single file
- `格式规范.md` - hot-zone capacity budget and cold-zone file templates

Full chat transcripts are no longer archived to bigmemory; keep only auditable summaries and project state.

**Read/write rules**: cold-zone daily files are append-only; hot-zone files are fully rewritten and must obey capacity budgets.

## .pipeline/ (project knowledge base)

- `terminology/` - terminology table
- `literature/` - literature library, with `index.md` as the main table
- `survey/` - survey library, one `.md` per topic
- `experiments/` - experiment ledger, one `YYYYMMDD_<topic>.md` per experiment run

## Memory Entry and Exit

**Entry (on demand)**: when AI decides project-history context is needed, proactively call the `memory-retrieval` skill.
**Exit (manual)**: when Dr Sun calls `/archive`, run triage, cold-zone archiving, and hot-zone refresh.

## When memory-retrieval Must Be Called

Do not bypass this by rationalization.

### Whitelist A - Triggered by Dr Sun's Question

- Asking current progress, project status, or what is happening now.
- Asking about last time, yesterday, earlier work, or previous days.
- Asking what remains unfinished, open decisions, or todos.
- Explicitly asking to recall, retrieve, look up previous records, or search memory.
- Any question whose meaning points to project history through words like now, recently, last time, previous, or still.

### Whitelist B - AI-Initiated Scenarios

- Preparing to write a paper section -> recall Contract, experiment results, and related literature.
- Preparing an experiment decision such as algorithm, hyperparameters, or simulation config -> recall previous configs and conclusions.
- Preparing cross-module code changes -> recall architecture decisions and existing conventions.
- Preparing a Research Contract -> recall existing contracts and hypothesis evolution.

### Blacklist - No Need To Call

- Pure code/tool syntax questions, such as how to write a Python function or use `git reset`.
- Dr Sun gives a single-line execution command, such as run tests, commit, or format this file.
- The request explicitly points to external resources, such as arXiv or a specific paper.
- The task can be closed within the current session and does not cross sessions.

### Anti-Rationalization Check

If you think any of the following, stop and call the skill:
- "I remember..."
- "It should be..."
- "Probably..."
- "I can just read the hot-zone files directly"
- "I already answered this earlier"

Typical violation: Dr Sun asks current status and AI directly reads three hot-zone files without using the memory skill.
