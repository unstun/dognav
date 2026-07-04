@AGENTS.md

1. Before editing files, run `git status --short`. If uncommitted changes already exist, decide whether they are related to the current task; leave unrelated changes untouched, and explain related high-risk changes to Dr Sun first.
2. Before editing code, paper text, or research records, create a local backup commit if the worktree already has related dirty diffs. Do not rely on automatic hooks.
3. When Dr Sun asks about git, commits, pushes, merges, or branches, check the current branch, latest commit, and `git status --short` first.
4. When Dr Sun asks about progress, status, last time, recent work, memory, or the hot zone, first read `bigmemory/热区/状态简报.md`, `bigmemory/热区/未关闭决策.md`, and `bigmemory/热区/近期改动.md`; search the cold zone only if needed.
5. After editing frontmatter documents under `.pipeline/survey/`, `.pipeline/contracts/`, `.pipeline/experiments/`, or `bigmemory/冷区/调研记录/`, change `reviewed: true` to `reviewed: false` if it was previously true.
6. After each meaningful change, run verification and commit according to `AGENTS.md`.
