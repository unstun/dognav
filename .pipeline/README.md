# .pipeline/ - Project Knowledge Base

`.pipeline/` stores long-lived structured project knowledge. It is not archived by day and does not expire automatically. It complements `bigmemory/`: `bigmemory/` tracks current session state, while `.pipeline/` tracks auditable facts, contracts, ledgers, and reviews.

## Database Inventory

| Directory | Purpose | Format |
|---|---|---|
| `terminology/` | terminology table | single Markdown table |
| `literature/` | literature index | Markdown |
| `survey/` | survey topics, conclusions, and sources | one `.md` per topic |
| `experiments/` | experiment ledger | one `.md` per run |
| `contracts/` | Research Contract pre-registration | one `.md` per experiment topic |
| `codex_tasks/` | manual Codex task package archive | one `.md` per task package |
| `goals/` | autonomous goal definitions | one `.md` per goal |
| `plans/` | implementation plans | one `.md` per plan |
| `audits/` | code/output acceptance audits | one `.md` per audit |
| `reviews/` | peer review records | one `.md` per review |
| `heartbeats/` | remote task heartbeat logs | log files |
| `incidents/` | incident records | one `.md` per incident |

## Current Entries

| Topic | Entry |
|---|---|
| terminology | `terminology/terminology.md` |
| Research Contract rules | `contracts/README.md` |
| nav literature index | `literature/README.md` |
| nav survey records | `survey/README.md` |
| nav experiment ledger | `experiments/README.md` |

## Maintenance Principles

- `draft` documents may be edited; `approved` or `frozen` Contracts must not be edited in place.
- Every claim must trace back to a Contract, code, logs, original text, or local files.
- Content from the walking repository may only be used as source reference, not as current nav conclusions.
