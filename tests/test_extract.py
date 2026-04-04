"""Tests for the extraction pipeline."""

from pathlib import Path
from lexwiki.extract.router import ingest_file
from lexwiki.extract.plain import extract_plain
from lexwiki.extract._html_to_md import html_to_markdown


def test_extract_plain(tmp_path):
    """Plain text passthrough."""
    src = tmp_path / "test.txt"
    src.write_text("Hello world. This is a test document.")
    text, pages = extract_plain(src)
    assert "Hello world" in text
    assert pages is None


def test_html_to_markdown():
    """Basic HTML to markdown conversion."""
    html = "<h1>Title</h1><p>Some <strong>bold</strong> text.</p>"
    md = html_to_markdown(html)
    assert "# Title" in md
    assert "**bold**" in md


def test_ingest_file_txt(tmp_path):
    """Ingest a plain text file."""
    src = tmp_path / "source" / "doc.txt"
    src.parent.mkdir()
    src.write_text("Legal document content here.")

    raw_dir = tmp_path / "raw"
    result = ingest_file(src, raw_dir)

    assert result.output.exists()
    assert result.format == "txt"
    assert result.word_count > 0

    content = result.output.read_text()
    assert "---" in content  # has frontmatter
    assert "Legal document content here." in content


def test_ingest_file_name_collision(tmp_path):
    """Handle duplicate filenames."""
    src = tmp_path / "doc.txt"
    src.write_text("First version.")

    raw_dir = tmp_path / "raw"
    r1 = ingest_file(src, raw_dir)

    src.write_text("Second version.")
    r2 = ingest_file(src, raw_dir)

    assert r1.output != r2.output
    assert r2.output.name == "doc_1.md"


def test_ingest_unsupported_format(tmp_path):
    """Reject unsupported file formats."""
    src = tmp_path / "file.xyz"
    src.write_text("data")

    import pytest
    with pytest.raises(ValueError, match="Unsupported format"):
        ingest_file(src, tmp_path / "raw")
