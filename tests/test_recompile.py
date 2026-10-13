"""Recompiling a source must update its own page, not leave duplicates (LLM stubbed)."""

import pytest

from lexwiki.compile.compiler import WikiCompiler
from lexwiki.config import LexWikiConfig
from lexwiki.types import DocMeta


@pytest.fixture
def compiler(tmp_path, monkeypatch):
    cfg = LexWikiConfig(raw_dir=tmp_path / "raw", wiki_dir=tmp_path / "wiki")
    cfg.raw_dir.mkdir()
    cfg.wiki_dir.mkdir()
    c = WikiCompiler(cfg)
    c.titles = {}
    monkeypatch.setattr(c, "_classify", lambda content: DocMeta(
        type="contract", title=c.titles.get(content, "Services Agreement"), jurisdiction="x",
    ))
    monkeypatch.setattr(c, "_compile_single", lambda content, meta, known: f"# {meta.title}\n{content}")
    return c


def _raw(c, name, text):
    path = c.raw_dir / name
    path.write_text(text, encoding="utf-8")
    return path


def _pages(c):
    return sorted(p.name for p in (c.wiki_dir / "contracts").glob("*.md"))


def test_recompile_overwrites_own_page(compiler):
    raw = _raw(compiler, "msa.md", "v1")
    compiler.compile_file(raw)
    raw.write_text("v2", encoding="utf-8")
    compiler.compile_file(raw)
    assert _pages(compiler) == ["services-agreement.md"]
    assert "v2" in (compiler.wiki_dir / "contracts" / "services-agreement.md").read_text()


def test_same_title_different_sources_kept_apart(compiler):
    compiler.compile_file(_raw(compiler, "msa.md", "a"))
    second = _raw(compiler, "msa_v2.md", "b")
    compiler.compile_file(second)
    compiler.compile_file(second)  # recompile of the suffixed page stays put
    assert len(_pages(compiler)) == 2


def test_retitled_source_drops_stale_page(compiler):
    raw = _raw(compiler, "msa.md", "v1")
    compiler.compile_file(raw)
    raw.write_text("v2", encoding="utf-8")
    compiler.titles["v2"] = "Master Services Agreement"
    compiler.compile_file(raw)
    assert _pages(compiler) == ["master-services-agreement.md"]


def test_legacy_timestamp_marker_is_tolerated(compiler):
    raw = _raw(compiler, "msa.md", "v1")
    marker = compiler._marker_path(raw)
    marker.parent.mkdir(parents=True)
    marker.write_text("2026-04-06T10:00:00+00:00")
    assert compiler._previous_page(raw) is None
    compiler.compile_file(raw)
    assert compiler._previous_page(raw) == compiler.wiki_dir / "contracts" / "services-agreement.md"
