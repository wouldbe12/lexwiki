"""Simple BM25-style keyword search over wiki pages as retrieval fallback."""

from __future__ import annotations

import math
import re
from pathlib import Path


def search_pages(query: str, wiki_dir: Path, top_k: int = 10) -> list[tuple[Path, float]]:
    """Search wiki pages by keyword relevance (BM25-like scoring).

    Returns list of (page_path, score) sorted by relevance, top_k results.
    """
    query_terms = _tokenize(query)
    if not query_terms:
        return []

    # Load all pages
    pages: list[tuple[Path, str]] = []
    for md_file in wiki_dir.rglob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8")
            pages.append((md_file, text.lower()))
        except (OSError, UnicodeDecodeError):
            continue

    if not pages:
        return []

    # Compute IDF for each query term
    n_docs = len(pages)
    idf: dict[str, float] = {}
    for term in query_terms:
        doc_freq = sum(1 for _, text in pages if term in text)
        idf[term] = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)

    # Score each page (BM25-like)
    k1 = 1.5
    b = 0.75
    avg_dl = sum(len(text.split()) for _, text in pages) / n_docs

    scored: list[tuple[Path, float]] = []
    for path, text in pages:
        words = text.split()
        dl = len(words)
        score = 0.0
        for term in query_terms:
            tf = text.count(term)
            if tf == 0:
                continue
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * dl / avg_dl)
            score += idf.get(term, 0) * numerator / denominator
        if score > 0:
            scored.append((path, score))

    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]


def _tokenize(text: str) -> list[str]:
    """Simple tokenization: lowercase, split on non-alphanumeric, remove short words."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    # Remove very common words
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "of", "in", "to", "for",
        "with", "on", "at", "by", "from", "as", "into", "about", "between",
        "through", "and", "or", "but", "not", "no", "if", "than", "that",
        "this", "these", "those", "what", "which", "who", "whom", "how",
        "all", "each", "every", "any", "some",
    }
    return [w for w in words if len(w) > 2 and w not in stopwords]
