@AGENTS.md

1. 修改文件前先运行 `git status --short`。如果已有未提交改动，先判断是否与当前任务相关；不相关的改动不碰，相关但风险高时先向 Dr Sun 说明。
2. 修改代码、论文或研究记录前，如果工作区已有相关 dirty diff，先做本地备份提交；不要依赖自动 hook。
3. Dr Sun 问 git、commit、push、merge、分支等问题时，先看当前分支、最近 commit 和 `git status --short`。
4. Dr Sun 问进度、状态、上次、最近、记忆、热区时，先读取 `bigmemory/热区/状态简报.md`、`bigmemory/热区/未关闭决策.md`、`bigmemory/热区/近期改动.md`，必要时再检索冷区。
5. 修改 `.pipeline/survey/`、`.pipeline/contracts/`、`.pipeline/experiments/` 或 `bigmemory/冷区/调研记录/` 下带 frontmatter 的文档后，如果原来有 `reviewed: true`，必须手动改为 `reviewed: false`。
6. 完成有意义变更后，按 `AGENTS.md` 要求做验证并提交。
