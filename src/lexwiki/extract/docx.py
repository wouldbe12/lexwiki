"""DOCX to markdown extraction using mammoth."""

from __future__ import annotations

from pathlib import Path


def extract_docx(source: Path) -> tuple[str, None]:
    """Convert DOCX/DOC to markdown.

    DOCX: Uses mammoth (HTML intermediate).
    DOC (legacy): Requires python-docx cannot handle .doc. Falls back to
    textract-style extraction or raises a clear error.

    Returns (markdown_text, None).
    """
    if source.suffix.lower() == ".doc":
        return _extract_legacy_doc(source)

    import mammoth
    from lexwiki.extract._html_to_md import html_to_markdown

    with open(source, "rb") as f:
        result = mammoth.convert_to_html(f)

    md = html_to_markdown(result.value)
    return md, None


def _extract_legacy_doc(source: Path) -> tuple[str, None]:
    """Extract text from legacy .doc files.

    Tries antiword first (common on Linux), then falls back to a raw
    binary text extraction as last resort.
    """
    import subprocess

    # Try antiword (apt install antiword)
    try:
        result = subprocess.run(
            ["antiword", str(source)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout, None
    except FileNotFoundError:
        pass

    # Try catdoc (apt install catdoc)
    try:
        result = subprocess.run(
            ["catdoc", str(source)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout, None
    except FileNotFoundError:
        pass

    # No binary fallback — it produces garbage
    raise ValueError(
        f"Cannot extract text from legacy .doc file: {source.name}\n"
        f"Install antiword: sudo apt install antiword (Linux) or brew install antiword (Mac)\n"
        f"Or convert the file to .docx first."
    )
