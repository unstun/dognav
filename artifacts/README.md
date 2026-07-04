# artifacts

`artifacts/` 保存 nav 训练、评估和展示产物。大文件默认不进 git；git 只记录小型索引和 manifest。

推荐结构：

```text
artifacts/
  YYYY-MM-DD_topic/
    README.md
    manifest.yaml
    tracked_checkpoints/
    tracked_logs/
    videos/
```

正式实验产物必须能回到：

- local commit
- remote path
- training command
- config
- source-hash manifest
- stdout/stderr log
