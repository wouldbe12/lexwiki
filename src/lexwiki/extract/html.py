"""HTML to markdown extraction using trafilatura."""

from __future__ import annotations

from pathlib import Path


def extract_html(source: Path) -> tuple[str, None]:
    """Extract main content from HTML file and convert to markdown.

    Returns (markdown_text, None).
    """
    import trafilatura

    raw_html = source.read_text(encoding="utf-8", errors="replace")
    md = trafilatura.extract(raw_html, output_format="markdown", include_tables=True)
    if not md:
        # Fallback: use our simple converter
        from lexwiki.extract._html_to_md import html_to_markdown

        md = html_to_markdown(raw_html)
    return md, None
