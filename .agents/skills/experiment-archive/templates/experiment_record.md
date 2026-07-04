---
origin: ai+local
reviewed: false
date: YYYY-MM-DD
experiment_id: <experiment_id>
version_alias: <version_alias>
status: archived
phase: <training|inference|evaluation|reproduction>
contract: <.pipeline/contracts/... or none>
source_of_truth: local_repo
remote_host: <host or none>
network: <used|skipped>
---

# Experiment Archive: <experiment_id>

## One-line identity

用一句人话写清这个实验是什么。不要只写代号。

例: `point-goal baseline 是第一轮 nav 合同下的 256-env smoke, 主权重 model_0800.pt, 不能当 sim-to-real 结论。`

## Minimum Facts

- What ran:
- Where it came from:
- Main artifact:
- Main result:
- Main caveat:
- Archive status:

## Artifact Map

保留关键产物即可。没有的项删掉; 缺失但重要的项写原因。

| What | Local path | Remote path | sha256 / status | Note |
|---|---|---|---|---|
| selected checkpoint |  |  |  |  |
| secondary checkpoint |  |  |  |  |
| tensorboard |  |  |  |  |
| stdout/stderr |  |  |  |  |
| env / agent config |  |  |  |  |
| videos / frames |  |  |  |  |
| source manifest |  |  |  |  |

## Claim Boundary

### Can say

-

### Cannot say

-

## Useful Details

下面栏目按需要保留、删除、改名或新增。

### Lineage

- Parent experiment:
- Parent checkpoint:
- Parent checkpoint sha256:
- Source snapshot / git commit:
- Training script:
- Training task ID:
- Eval task ID(s):

### Terrain And Distribution

- Training terrain:
- Eval terrain:
- Command distribution:
- Domain randomization:
- Important difference from parent:

### Contract

- Contract:
- Success signal:
- Failure signal:

### Commands

```bash
conda activate <env>
<training or inference command>
```

### Metrics And Curves

- Main reward / score:
- Best iteration:
- Selected iteration:
- Collapse / anomaly:
- Plot path:
- CSV path:

### Visual Review

- Video path:
- Human-readable observation:
- Failure modes:
- Boundary scenes:

### Double-End Sync Gate

- Local repo is source of truth: <yes|no>.
- Remote-only changes exist: <yes|no>.
- All required artifacts synced back: <yes|no>.
- Result package exists: artifacts/<experiment_id>/ <yes|no>.
- Key files tracked by git: <yes|no>.
- Files too large for git: <none or list with reason>.

### Web Verification

- Network used: <yes|no>.
- Sources:
  - <URL> -- <claim supported>
- External facts that affect the archive:

## Freeform Notes

写任何模板没有覆盖但人以后会关心的东西: 直觉、视频观感、踩坑、下一步想法、命名争议。

## Human Notes

<Dr Sun comments or later review notes.>
