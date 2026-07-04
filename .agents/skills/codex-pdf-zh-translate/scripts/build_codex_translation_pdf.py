#!/usr/bin/env python3
"""Build a Chinese reading PDF from Codex-translated page Markdown files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def _load_reportlab():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: reportlab. Install with `python3 -m pip install reportlab`."
        ) from exc
    return A4, pdfmetrics, UnicodeCIDFont, canvas


def _page_number(path: Path) -> int:
    match = re.search(r"page_(\d+)", path.stem)
    return int(match.group(1)) if match else 0


def _wrap_text(text: str, font_name: str, font_size: int, max_width: float, pdfmetrics) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            candidate = current + char
            if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = char
        if current:
            lines.append(current)
    return lines


def build_pdf(translations_dir: Path, output_pdf: Path, title: str) -> None:
    A4, pdfmetrics, UnicodeCIDFont, canvas = _load_reportlab()
    font_name = "STSong-Light"
    pdfmetrics.registerFont(UnicodeCIDFont(font_name))

    page_files = sorted(translations_dir.glob("page_*.md"), key=_page_number)
    if not page_files:
        raise SystemExit(f"No translation files found in {translations_dir}")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_pdf), pagesize=A4)
    width, height = A4
    margin_x = 46
    margin_top = 50
    margin_bottom = 42
    body_size = 10
    title_size = 14
    line_height = 16
    max_width = width - margin_x * 2

    for file_index, page_file in enumerate(page_files, start=1):
        source_page = _page_number(page_file)
        text = page_file.read_text(encoding="utf-8").strip()
        c.setFont(font_name, title_size)
        c.drawString(margin_x, height - margin_top, title)
        c.setFont(font_name, 9)
        c.drawRightString(width - margin_x, height - margin_top, f"原文第 {source_page} 页")

        y = height - margin_top - 34
        c.setFont(font_name, body_size)
        for line in _wrap_text(text, font_name, body_size, max_width, pdfmetrics):
            if y < margin_bottom:
                c.showPage()
                c.setFont(font_name, 9)
                c.drawRightString(width - margin_x, height - margin_top, f"原文第 {source_page} 页续")
                y = height - margin_top - 24
                c.setFont(font_name, body_size)
            if line:
                c.drawString(margin_x, y, line)
            y -= line_height

        c.setFont(font_name, 8)
        c.drawCentredString(width / 2, 24, f"{file_index}")
        c.showPage()

    c.save()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("translations_dir", type=Path)
    parser.add_argument("output_pdf", type=Path)
    parser.add_argument("--title", default="Codex 中文通读版")
    args = parser.parse_args()

    build_pdf(
        args.translations_dir.expanduser().resolve(),
        args.output_pdf.expanduser().resolve(),
        args.title,
    )
    print(f"output_pdf={args.output_pdf.expanduser().resolve()}")


if __name__ == "__main__":
    main()
