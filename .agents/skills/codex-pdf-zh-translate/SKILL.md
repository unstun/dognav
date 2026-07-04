---
name: codex-pdf-zh-translate
description: Translate user-provided academic PDFs into Chinese by having Codex do the translation itself, with local extraction and PDF rebuilding helpers. Use when Dr Sun asks for Codex/self PDF translation, Chinese reading PDFs, avoiding external translation APIs, or continuing an interrupted PDF translation.
---

# Codex PDF Chinese Translation

## Scope

Use this skill for user-provided academic PDFs when the translation should be done by Codex itself. Do not call external translation services, do not use configured API keys, and do not paste long full translations into chat. Produce local files under the project instead.

The default output is a Chinese study-reading PDF. It preserves page order, headings, citations, equations in text form, captions, and terminology as well as the extractor allows. It is not a pixel-identical overlay. Use `pdf2zh` only when the user explicitly asks for external layout-preserving translation.

## Quick Start

```bash
python3 .agents/skills/codex-pdf-zh-translate/scripts/extract_pdf_for_codex.py \
  /path/to/paper.pdf \
  artifacts/literature_zh/codex_self/YYYY-MM-DD/paper_stem
```

Translate each `pages/page_###.txt` into Chinese and write:

```text
artifacts/literature_zh/codex_self/YYYY-MM-DD/paper_stem/translations/page_###.md
```

Then build the PDF:

```bash
python3 .agents/skills/codex-pdf-zh-translate/scripts/build_codex_translation_pdf.py \
  artifacts/literature_zh/codex_self/YYYY-MM-DD/paper_stem/translations \
  artifacts/literature_zh/codex_self/YYYY-MM-DD/paper_stem/paper_stem_codex_zh.pdf
```

## Translation Rules

1. Work page by page. Check existing `translations/page_###.md` first and resume from the first missing page.
2. Translate meaning, not sentence shape. Keep academic tone, equations, variable names, citation markers, algorithm names, dataset names, and robot/control terms stable.
3. Keep section labels readable in Chinese: `摘要`, `引言`, `方法`, `实验`, `结果`, `讨论`, `结论`, `参考文献`.
4. Leave uncertain OCR fragments marked as `[原文识别不清]` rather than inventing content.
5. For tables and equations, preserve structure in Markdown when exact layout cannot be rebuilt.
6. For figures, translate captions and refer to the original figure number; do not redraw figures unless requested.

## Workflow

1. Extract text with `extract_pdf_for_codex.py`.
2. Inspect `manifest.json` for page count and text length. If a page has little text, render that page with `pdftoppm` and inspect visually.
3. Translate pages into `translations/page_###.md`. Keep each page file self-contained and start with `# 第 N 页`.
4. Build the Chinese PDF with `build_codex_translation_pdf.py`.
5. Verify with `pdfinfo`, render representative pages with `pdftoppm`, and inspect PNGs for missing glyphs, clipped text, broken page order, and unreadable tables.
6. Record output paths and unresolved OCR/layout issues in a short note beside the PDF.

## Resume Rules

If interrupted, list existing translation files and continue from the first missing page:

```bash
find artifacts/literature_zh/codex_self -path '*/translations/page_*.md' | sort
```

Do not restart completed pages unless the user asks for revision.
