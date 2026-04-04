"""Query engine — answers questions using the wiki as context (no vector DB)."""

from __future__ import annotations

import re
from pathlib import Path

from lexwiki.config import LexWikiConfig
from lexwiki.llm.client import complete, complete_structured
from lexwiki.llm.tokens import estimate_tokens, truncate_to_tokens

_SELECT_SYSTEM = "You are a legal research assistant. Respond only with valid JSON."

_SELECT_PROMPT = """\
Given this question and the wiki index, select the most relevant pages to answer it.

Question: {question}
{scope_line}

Master Index:
---
{index_content}
---

Return a JSON array of page filenames (max 15), most relevant first:
["contracts/master-services-agreement.md", "statutes/gdpr-overview.md"]

Only include pages that are likely to contain information relevant to the question.
"""

_ANSWER_SYSTEM = """\
You are a legal knowledge base assistant. Answer questions using ONLY the provided wiki pages as context.

Rules:
- Cite sources using [[page-name]] notation (the filename without extension)
- If the answer cannot be fully determined from the context, say so explicitly
- Be precise about legal terms, dates, obligations, and parties
- Do not speculate beyond what the documents state
- Structure longer answers with headings and bullet points
"""

_ANSWER_PROMPT = """\
Answer this legal question using the provided wiki pages.

Question: {question}

Context pages:
---
{context}
---

Provide a thorough answer with [[page-name]] citations.
"""


class QueryEngine:
    """Answer questions by reading wiki indexes, selecting pages, and synthesizing answers."""

    def __init__(self, config: LexWikiConfig):
        self.config = config
        self.wiki_dir = config.wiki_dir

    def query(self, question: str, scope: str | None = None) -> str:
        """Answer a question against the wiki.

        1. Read the master index to understand what's available
        2. Ask the LLM to select relevant pages
        3. Load those pages
        4. Ask the LLM to synthesize an answer with citations
        """
        # Step 1: Read indexes
        index_content = self._read_indexes()
        if not index_content.strip():
            return "The wiki is empty. Run `lexwiki compile` first to build the knowledge base."

        # Step 2: Select relevant pages (LLM picks from index, keyword search as fallback)
        selected = self._select_pages(question, index_content, scope)
        if not selected:
            selected = self._keyword_fallback(question)
        if not selected:
            return "No relevant pages found for this question. Try broadening your query."

        # Step 3: Load page content
        context = self._load_pages(selected)

        # Step 4: Synthesize answer
        prompt = _ANSWER_PROMPT.format(question=question, context=context)
        answer = complete(prompt, system=_ANSWER_SYSTEM, config=self.config.llm)
        return answer

    def _read_indexes(self) -> str:
        """Read the master index and type index for page selection."""
        parts = []
        for idx_name in ["_index.md", "_by_type.md"]:
            idx_path = self.wiki_dir / idx_name
            if idx_path.exists():
                parts.append(idx_path.read_text(encoding="utf-8"))

        return "\n\n".join(parts)

    def _select_pages(
        self, question: str, index_content: str, scope: str | None
    ) -> list[str]:
        """Ask the LLM to pick relevant pages from the index."""
        scope_line = f"Scope filter: {scope}" if scope else "No scope filter."

        prompt = _SELECT_PROMPT.format(
            question=question,
            scope_line=scope_line,
            index_content=truncate_to_tokens(index_content, 8000),
        )

        try:
            result = complete_structured(prompt, system=_SELECT_SYSTEM, config=self.config.llm)
            if isinstance(result, list):
                return [str(p) for p in result[:15]]
        except (ValueError, KeyError):
            pass
        return []

    def _keyword_fallback(self, question: str) -> list[str]:
        """BM25 keyword search as fallback when LLM page selection fails."""
        from lexwiki.query.search import search_pages

        results = search_pages(question, self.wiki_dir, top_k=10)
        return [str(p.relative_to(self.wiki_dir)) for p, _ in results]

    def _load_pages(self, page_paths: list[str]) -> str:
        """Load selected wiki pages, fitting within token budget."""
        budget = self.config.llm.max_tokens * 6  # Leave room for answer
        parts = []
        total_tokens = 0

        for rel_path in page_paths:
            full_path = self.wiki_dir / rel_path
            if not full_path.exists():
                # Try finding by stem
                matches = list(self.wiki_dir.rglob(f"{Path(rel_path).stem}.md"))
                if matches:
                    full_path = matches[0]
                else:
                    continue

            try:
                text = full_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            tokens = estimate_tokens(text)
            if total_tokens + tokens > budget:
                text = truncate_to_tokens(text, budget - total_tokens)
                parts.append(f"### {full_path.stem}\n{text}")
                break

            parts.append(f"### {full_path.stem}\n{text}")
            total_tokens += tokens

        return "\n\n---\n\n".join(parts)
