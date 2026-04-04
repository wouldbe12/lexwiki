"""Plain text and markdown passthrough."""

from __future__ import annotations

from pathlib import Path


def extract_plain(source: Path) -> tuple[str, None]:
    """Read plain text or markdown files as-is.

    Returns (text_content, None).
    """
    text = source.read_text(encoding="utf-8", errors="replace")
    return text, None
