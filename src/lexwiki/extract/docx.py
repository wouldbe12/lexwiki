"""DOCX to markdown extraction using mammoth."""

from __future__ import annotations

from pathlib import Path


def extract_docx(source: Path) -> tuple[str, None]:
    """Convert DOCX to markdown via mammoth (HTML intermediate).

    Returns (markdown_text, None).
    """
    import mammoth
    from lexwiki.extract._html_to_md import html_to_markdown

    with open(source, "rb") as f:
        result = mammoth.convert_to_html(f)

    md = html_to_markdown(result.value)
    return md, None
