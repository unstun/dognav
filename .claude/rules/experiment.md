---
paths: ["2_experiment/**", "configs/**"]
---

# 实验规则

## 硬规则

- MUST:训练/推理参数放在对应 nav baseline 子项目的 `configs/` 目录，或放在 Contract 明确指定的位置。
- MUST:消融实验结束后记录到 `.pipeline/experiments/`。
- MUST:远端训练/推理前必须完整同步代码；远端如有临时修改,结束前必须回流本地同路径并由本地 `git diff` 呈现；严禁出现远端跑通但本地无对应代码的 remote-only 状态。
- MUST:推理前必须确认 checkpoint 文件正确,不能依赖"默认最新"。
- MUST:SSH 远程执行 conda 必须 `conda run --cwd <项目绝对路径>/2_experiment -n <env> python ...`。
- MUST:实验代码按 nav baseline 子项目声明 Python module。默认目录为 `2_experiment/nav_baselines/<topic>/`；复用外部或 walking 代码时，在 `2_experiment/source_references/<name>/_meta/` 记录来源。

## 环境

| 平台 | 用途 | 说明 |
| ---- | ---- | ---- |
| Mac (Apple Silicon) | 代码开发 / 论文写作 | PyTorch CPU 版,`KMP_DUPLICATE_LIB_OK=TRUE` 已设 |
| Ubuntu (远程 GPU) | 训练 + 推理 | RTX 4090,Isaac Lab / MuJoCo |

## 常用命令

```bash
PROJ=$HOME/machine-dog-nav; EXP=$PROJ/2_experiment; ENV=<conda_env>

# 入口走 nav baseline 子项目模块:
mkdir -p "$EXP/runs"
nohup conda run --cwd $EXP -n $ENV python -m <nav_module>.cli.train \
  --profile $PROFILE \
  > $EXP/runs/${PROFILE}_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

## 阶段顺序

实验推进严格按以下顺序，不可跳步：

1. **Baseline 复现** → 建立可靠锚点
2. **Research Contract** → 锁定 hypothesis + success/failure signals（硬规则 #20）
3. **实验执行** → 对照 Contract 判定结果

## Baseline 复现

- MUST:实验前检查已有数据集和环境文档，不盲目重新下载。
- MUST:复现工作走 sub-agent 执行，主 session 只收结果摘要。
- MUST:复现成功后记录到 .pipeline/experiments/，成为后续实验的锚点。

## 实验前检查

- 检查阶段顺序：baseline 已复现 → Contract 已提交
- 检查 .pipeline/contracts/ 是否有对应的 Research Contract（硬规则 #20）
- 检查数据集是否已存在于已知路径
- 检查环境是否已搭建完成
