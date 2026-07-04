#!/usr/bin/env python3
"""Extract user-provided PDF pages into text files for Codex translation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _load_reader():
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: pypdf. Install with `python3 -m pip install pypdf`."
        ) from exc
    return PdfReader


def extract_pdf(input_pdf: Path, output_dir: Path) -> dict:
    PdfReader = _load_reader()
    reader = PdfReader(str(input_pdf))

    pages_dir = output_dir / "pages"
    translations_dir = output_dir / "translations"
    pages_dir.mkdir(parents=True, exist_ok=True)
    translations_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source_pdf": str(input_pdf),
        "output_dir": str(output_dir),
        "page_count": len(reader.pages),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages": [],
    }

    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        page_path = pages_dir / f"page_{idx:03d}.txt"
        page_path.write_text(
            f"# Page {idx}\n\n{text.strip()}\n",
            encoding="utf-8",
        )
        manifest["pages"].append(
            {
                "page": idx,
                "text_file": str(page_path),
                "char_count": len(text),
            }
        )

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    input_pdf = args.input_pdf.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not input_pdf.exists():
        raise SystemExit(f"PDF not found: {input_pdf}")

    manifest = extract_pdf(input_pdf, output_dir)
    print(f"source={manifest['source_pdf']}")
    print(f"output_dir={manifest['output_dir']}")
    print(f"page_count={manifest['page_count']}")
    print(f"manifest={output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
