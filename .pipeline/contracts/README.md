# Research Contracts

Pre-registration commitments before experiments. Once submitted and approved by Dr Sun, a Contract must not be edited in place. If changes are needed, create v2 and state the reason in the file header.

## Current Status

This repository has no approved nav Contract yet. Formal training, long remote runs, and paper claims must wait until the first nav Contract reaches `approved` or `frozen`.

## Template

~~~yaml
---
version: v1
date: YYYY-MM-DD
status: draft
origin: <ai_only|ai+web|human>
reviewed: false
baseline: <baseline name or none>
---
~~~

### Status Values

- `draft`: in drafting; may still be edited.
- `approved`: reviewed and approved by Dr Sun; may be used as experiment basis.
- `frozen`: already in execution or cited by a paper/review; changes require a new v2.

~~~markdown
# [Experiment Topic] Research Contract

## Research Question
[What question this nav experiment answers]

## Hypothesis
[Explicit hypothesis statement]

## Method
[Method description, including whether the walking base policy is frozen, fine-tuned, or unused]

## Inputs and Outputs
- Inputs:
- Outputs:

## Success Signals
- Signal 1: [specific metric + threshold]
- Signal 2:

## Failure Signals (defined independently; not the opposite of success)
- Signal 1: [specific failure condition]
- Signal 2:

## Ablation Plan
| Experiment | Expected Result | Judgment Standard |
|---|---|---|
| ... | ... | ... |

## Hyperparameters
[Locked hyperparameter list]

## Data / Terrain Split
[Train/validation/test scene split]

## Evidence To Archive
- code commit:
- config:
- stdout/stderr log:
- checkpoint:
- evaluation video:
- metrics:
~~~
