"""PDF to markdown extraction using pymupdf4llm."""

from __future__ import annotations

from pathlib import Path


def extract_pdf(source: Path) -> tuple[str, int]:
    """Convert PDF to markdown. Returns (markdown_text, page_count)."""
    import pymupdf4llm
    import pymupdf

    doc = pymupdf.open(str(source))
    page_count = len(doc)
    doc.close()

    md = pymupdf4llm.to_markdown(str(source))
    return md, page_count
