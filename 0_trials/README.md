# 0_trials

`0_trials/` 保存探索性脚本、候选可视化、当天诊断代码和一次性 HTML/Notebook。

这里的内容属于探索记录，不等同于正式实验代码。跑通且需要复用的脚本，迁移到 `2_experiment/`；确认成为评估协议或 baseline 后，再进入 `.pipeline/experiments/` 台账。

## 推荐结构

```text
0_trials/
  YYYY-MM-DD/
    README.md
    <topic_name>/
      README.md
      manifest.yaml
      index.html
      probe_xxx.py
```

## 约定

1. 每天新增一个日期目录，命名 `YYYY-MM-DD`。
2. 主题目录命名 `<snake_case_topic>/`。
3. 主题目录至少包含 `README.md`，说明用途、来源和使用边界。
4. 有可量化产物时配 `manifest.yaml`，列出 source 指针和 sha256。
5. 本目录不能作为论文 claim 或正式实验依据。
