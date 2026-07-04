# 2_experiment

`2_experiment/` 放 nav 实验代码。当前还没有 approved Contract，因此这里只保留骨架。

```text
2_experiment/
├── nav_baselines/          # nav baseline 实现
└── source_references/      # 外部仓库或 walking 基础仓库的轻量索引
```

## 原则

- 先写 Research Contract，再写正式训练代码。
- 复用 walking policy 前必须记录来源 commit、checkpoint、冻结/微调边界。
- 外部仓库放 `source_references/<name>/upstream/`，该目录默认 gitignored。
