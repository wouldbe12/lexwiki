"""Shared types for LexWiki."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DocMeta:
    """Metadata extracted during document classification."""

    type: str  # contract | statute | case_law | memo | regulation | other
    title: str
    jurisdiction: str
    parties: list[str] = field(default_factory=list)
    effective_date: str | None = None
    subject_areas: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class LintIssue:
    """A single issue found during wiki linting."""

    severity: str  # error | warning | info
    category: str  # expired_citation | inconsistent_clause | missing_term | broken_backlink | stale_page
    file: str
    line: int | None
    message: str
    suggestion: str


@dataclass
class CompileStats:
    """Statistics from a compile run."""

    pages_created: int = 0
    pages_updated: int = 0
    indexes_rebuilt: int = 0
    backlinks_inserted: int = 0


@dataclass
class IngestResult:
    """Result of ingesting a single document."""

    source: Path
    output: Path
    format: str
    word_count: int
    page_count: int | None = None
