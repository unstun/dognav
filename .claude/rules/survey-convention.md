---
paths:
  - 1_survey/**
  - .pipeline/literature/**
---

# 调研材料管理规范

## 1_survey/ 目录结构

```
1_survey/
├── README.md                                # 总索引（必须维护）
├── papers/                                  # 论文 PDF（跨轮次共享）
│   └── AuthorYear_ShortTitle.pdf
└── YYYY-MM-DD_<目的短语>/                    # 每轮调研一个目录
    ├── gemini-deep-research.md
    ├── chatgpt-deep-research.md
    ├── grok-deep-research.md
    └── ...                                  # 该轮次的其他笔记
```

## 命名规范

### 调研轮次目录
`YYYY-MM-DD_<目的短语>/`，目的用小写英文短横线连接：
- `2026-04-16_quadruped-drl-landscape/`
- `2026-05-01_reward-shaping-deep-dive/`

### 轮次内报告文件
`<来源>-deep-research.md`，来源即模型/平台名：
- `gemini-deep-research.md`
- `chatgpt-deep-research.md`
- `grok-deep-research.md`
- 手动笔记用 `notes.md` 或 `<主题>-notes.md`

### 论文 PDF
`AuthorYear_ShortTitle.pdf`，存 `papers/`（跨轮次共享），与 `3_paper/references.bib` 的 CitationKey 一致。

## README.md 索引表维护

每次新建调研轮次后必须更新 `1_survey/README.md`，包含：

| 字段 | 说明 |
|------|------|
| 目录 | 轮次目录名（反引号包裹） |
| 日期 | YYYY-MM-DD |
| 目的 | 一句话说明为什么做这轮调研 |
| 来源 | 用了哪些模型/平台 |
| 状态 | ✅ 完成 / 🔄 进行中 / ❌ 待开始 |
