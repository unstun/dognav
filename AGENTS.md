# Lite3 Quadruped Navigation DRL Research Project

> Scope: `/Users/sun/tongbu/study/phdproject/machine-dog-nav/**` · Source of truth: this file (`AGENTS.md`); `CLAUDE.md` imports it through `@AGENTS.md`.

## Identity and Protocol

This is a long-running PhD research project. The goal is to develop quadruped navigation capability on top of an existing quadruped locomotion base. Each session handles one task only. Protocol: read state -> do one task -> write state -> stop.

Current stage: planning and literature survey. Before entering the experiment stage, `.pipeline/contracts/<topic>.md` must exist and its `status` must be `approved` or `frozen`.

## Boundary With the Walking Repository

1. `machine-dog` is the locomotion base repository and contains walking, gait, and parkour training history.
2. `machine-dog-nav` is a new-direction repository. It does not inherit old experiment conclusions by default.
3. Old checkpoints, rewards, terrain curricula, and experiment evidence may only be used as source references. They must not be written as nav results.
4. If a walking policy is reused as the base policy, the nav Research Contract must state the source, weights, commit, freeze/fine-tune boundary, and failure signals.

## Operating Notes

1. **AI is unreliable by default**: treat every AI output as untrusted until verified.
2. **Context Is All You Need**: the quality of the current session context determines model performance; polluted context derails the task.
3. **Literature survey means building expert context**: survey work is not collecting a few papers; it must build auditable expert context for the nav direction.
4. **Pre-registration prevents rationalization**: before experiments, lock the hypothesis, success signals, and failure signals.
5. Explanations for Dr Sun must be understandable to a human reader and should avoid AI jargon.
6. Keep questioning earlier conclusions. Do not treat early judgments as settled unless Dr Sun has confirmed them.

### Think Before Editing

Before editing code or research records, state the current assumption. If information is insufficient, pause, name the unclear points, and confirm with Dr Sun before continuing. If the request has multiple plausible interpretations, explain the differences and impact.

### Prefer Simplicity

Write only the code and documentation needed for the current problem. Do not add side features, speculative configuration, or future-proofing that expands scope.

### Keep Edits Narrow

Modify only the files required for the task. Prefer the existing style. Record unrelated dead code if needed, but do not delete it without being asked.

### Verify Against the Goal

Before starting, convert the task into checkable goals. Bug fixes need a reproduction or minimal check. Documentation changes need path, stale-name, and evidence-boundary checks. Experiments must be judged against the Contract.

## Hard Rules

### Core Behavior

1. MUST: Start every reply with `Dr Sun,`.
2. MUST: Reply in Chinese by default. Questions addressed to Dr Sun must be in Chinese.
3. STYLE: When an English technical term first appears, provide a Chinese explanation when useful, for example `trajectory adherence（轨迹遵循）`.
4. MUST: Optimize code and comments for human review.
5. MUST: Plan before editing files; for large tasks, write the plan before starting.

### Research Discipline

6. MUST: Create a git commit after each meaningful change. Small commits are allowed as process checkpoints, but before pushing, remind Dr Sun to decide whether to squash them into one clear commit.
7. MUST: Ask Dr Sun first when research decisions, technical choices, or experiment designs are uncertain.
8. MUST: Read before answering. For internal information, check local files and Auggie MCP first. For web access, use `smart-search-cli` by default. If something cannot be confirmed, say `I do not know`.
9. MUST: For complex tasks, consider multi-agent verification by default. If the tool layer cannot launch a subagent, say so and replace it with locally auditable verification.
10. MUST: Handle one task per session. After finishing, write state and stop. Do not mix planning, experiment+analysis, and writing stages.

### Code and Tools

11. MUST: Prefer Auggie MCP for code search; use `rg` only when Auggie is unavailable.
12. MUST: Store literature PDFs, datasets, and experiment artifacts inside the project. Paper PDFs go under `1_survey/papers/<CitationKey>.pdf`.
13. MUST: `CLAUDE.md` and `AGENTS.md` are written for AI agents, so prioritize parseability and executability. Other outputs should prioritize human readability.

### Safety Floor

14. MUST: When the user challenges a claim, re-check the original source facts before responding. Do not blindly agree.
15. MUST: Do not claim `fixed` or `complete` unless verification has been run.

### Research Contract

16. MUST: Before entering the experiment stage, a Research Contract (`.pipeline/contracts/<topic>.md`) must exist. `draft` must not be used as experiment basis.
17. MUST: The Contract must independently define the hypothesis, success signals, and failure signals. Failure is not just the opposite of success.
18. MUST: Once a Contract is `approved`, it must not be edited in place. If changes are needed, create v2 and state the reason.
19. MUST: Later code, reviews, and paper claims must use the Contract as the only yardstick.

### Source of Truth and Sync Gate

20. MUST: The local repo is the only source of truth for code. Remote directories are execution copies only.
21. MUST: Temporary remote diagnostic edits are allowed, but final changes must be synced back to the same local paths and shown by local `git diff`.
22. MUST: If remote-only changes exist or local/remote consistency cannot be proven, experiment and ledger claims are FAIL.
23. MUST: After remote training or inference, sync back local code, checkpoints, videos, key frames, configs, complete stdout/stderr logs, training commands, and a source-hash manifest.
24. STYLE: New files and artifacts should include time, topic, and purpose in their names. Avoid generic root directories such as `output/`, `outputs/`, or `logs/`.
25. MUST: `.pipeline/terminology/terminology.md` is the only source of truth for terminology. Before introducing a new term, check the literature and the local terminology table.

## Directory Conventions

- `0_trials/`: exploratory scripts, one-off HTML/Notebook files, and candidate visualizations.
- `1_survey/`: nav literature surveys, paper PDFs, and paper markdown.
- `2_experiment/`: nav experiment code and source references.
- `3_paper/`: paper writing.
- `4_assets/`: maps, scenes, sensors, and visualization assets.
- `5_algorithm/`: algorithm notes.
- `artifacts/`: checkpoints, logs, videos, evaluation reports, and other experiment artifacts.
- `bigmemory/`: session memory, including hot and cold zones.
- `.pipeline/`: long-lived structured knowledge base.
