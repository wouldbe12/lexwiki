"""Insert [[backlinks]] into wiki pages based on page title matching."""

from __future__ import annotations

import re
from pathlib import Path


def build_page_index(wiki_dir: Path) -> dict[str, str]:
    """Build a mapping of page titles (lowercase) to their link names.

    Scans all .md files in wiki_dir (excluding index files starting with _).
    Returns {lowercase_title: link_name} where link_name is the filename stem.
    """
    index: dict[str, str] = {}
    for md_file in wiki_dir.rglob("*.md"):
        if md_file.name.startswith("_"):
            continue
        stem = md_file.stem
        # Use the stem as-is for the link
        index[stem.lower().replace("-", " ")] = stem
        # Also try extracting title from frontmatter
        title = _extract_title(md_file)
        if title:
            index[title.lower()] = stem
    return index


def _extract_title(md_file: Path) -> str | None:
    """Extract title from YAML frontmatter."""
    try:
        text = md_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None

    for line in match.group(1).split("\n"):
        if line.startswith("title:"):
            title = line.split(":", 1)[1].strip().strip("\"'")
            return title
    return None


def insert_backlinks(wiki_dir: Path) -> int:
    """Scan all wiki pages and insert [[backlinks]] where page titles are mentioned.

    Only inserts links where they don't already exist. Does not link a page to itself.
    Returns the count of backlinks inserted.
    """
    page_index = build_page_index(wiki_dir)
    if not page_index:
        return 0

    count = 0
    for md_file in wiki_dir.rglob("*.md"):
        if md_file.name.startswith("_"):
            continue

        current_stem = md_file.stem
        try:
            content = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        original = content

        # Split into frontmatter and body
        fm_match = re.match(r"^(---\n.*?\n---\n)(.*)", content, re.DOTALL)
        if fm_match:
            frontmatter, body = fm_match.group(1), fm_match.group(2)
        else:
            frontmatter, body = "", content

        for title_lower, link_name in page_index.items():
            # Don't link to self
            if link_name == current_stem:
                continue
            # Don't insert if already linked
            if f"[[{link_name}]]" in body:
                continue
            # Find mentions of the title (case-insensitive, whole word)
            pattern = re.compile(r"\b" + re.escape(title_lower) + r"\b", re.IGNORECASE)
            if pattern.search(body):
                # Replace first occurrence only
                def _replace_first(m):
                    return f"[[{link_name}|{m.group(0)}]]"

                body, n = pattern.subn(_replace_first, body, count=1)
                if n > 0:
                    count += 1

        new_content = frontmatter + body
        if new_content != original:
            md_file.write_text(new_content, encoding="utf-8")

    return count
