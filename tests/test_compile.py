"""Tests for the compile pipeline (non-LLM parts)."""

from lexwiki.compile.chunker import chunk_text
from lexwiki.compile.backlinker import build_page_index


def test_chunk_text_small():
    """Small text should not be chunked."""
    text = "Short document."
    chunks = chunk_text(text, max_tokens=1000)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_large():
    """Large text should be split into multiple chunks."""
    # Create text with ~5000 tokens (~20000 chars)
    paragraphs = [f"Paragraph {i}. " + "word " * 100 for i in range(40)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, max_tokens=2000, overlap_tokens=200)
    assert len(chunks) > 1
    # Each chunk should be within budget (approximately)
    for chunk in chunks:
        assert len(chunk) < 10000  # ~2500 tokens * 4 chars


def test_build_page_index(tmp_path):
    """Build page index from wiki directory."""
    wiki_dir = tmp_path / "wiki"
    contracts = wiki_dir / "contracts"
    contracts.mkdir(parents=True)

    (contracts / "msa.md").write_text("---\ntitle: Master Services Agreement\n---\nContent.")
    (contracts / "nda.md").write_text("---\ntitle: Non-Disclosure Agreement\n---\nContent.")
    (wiki_dir / "_index.md").write_text("# Index")  # should be excluded

    index = build_page_index(wiki_dir)
    assert "msa" in index
    assert "nda" in index
    assert "master services agreement" in index
    assert "_index" not in index
