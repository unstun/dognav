---
paths:
  - 1_survey/**
  - .pipeline/literature/**
---

# Survey Material Management Rules

## 1_survey/ Directory Structure

```text
1_survey/
|-- README.md                                # Master index; must be maintained.
|-- papers/                                  # Paper PDFs shared across rounds.
|   `-- AuthorYear_ShortTitle.pdf
`-- YYYY-MM-DD_<purpose-phrase>/             # One directory per survey round.
    |-- gemini-deep-research.md
    |-- chatgpt-deep-research.md
    |-- grok-deep-research.md
    `-- ...                                  # Other notes for this round.
```

## Naming Rules

### Survey Round Directory

`YYYY-MM-DD_<purpose-phrase>/`, with the purpose phrase in lowercase English kebab-case:
- `2026-04-16_quadruped-drl-landscape/`
- `2026-05-01_reward-shaping-deep-dive/`

### Report Files Within a Round

`<source>-deep-research.md`, where source is the model/platform name:
- `gemini-deep-research.md`
- `chatgpt-deep-research.md`
- `grok-deep-research.md`
- Manual notes use `notes.md` or `<topic>-notes.md`.

### Paper PDFs

`AuthorYear_ShortTitle.pdf`, stored under `papers/` and matching the CitationKey in `3_paper/references.bib`.

## README.md Index Maintenance

Every time a survey round directory is created, update `1_survey/README.md` with:

| Field | Meaning |
|---|---|
| Directory | round directory name, wrapped in backticks |
| Date | YYYY-MM-DD |
| Purpose | one sentence explaining why this survey round exists |
| Sources | which models/platforms were used |
| Status | done / in progress / todo |
