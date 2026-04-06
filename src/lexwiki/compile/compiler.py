"""WikiCompiler — orchestrates the compilation of raw markdown into a structured wiki."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from lexwiki.compile.backlinker import insert_backlinks
from lexwiki.compile.chunker import chunk_text
from lexwiki.compile.prompts.classify import CLASSIFY_PROMPT, CLASSIFY_SYSTEM
from lexwiki.compile.prompts.index import (
    CLAUSE_LIBRARY_PROMPT,
    INDEX_SYSTEM,
    JURISDICTION_INDEX_PROMPT,
    MASTER_INDEX_PROMPT,
    PARTY_INDEX_PROMPT,
    PRECEDENT_MAP_PROMPT,
    TYPE_INDEX_PROMPT,
)
from lexwiki.compile.prompts.summarize import (
    SUMMARIZE_CHUNKED_PROMPT,
    SUMMARIZE_PROMPT,
    SUMMARIZE_SYSTEM,
)
from lexwiki.config import LexWikiConfig
from lexwiki.llm.client import complete, complete_structured
from lexwiki.llm.tokens import estimate_tokens
from lexwiki.types import CompileStats, DocMeta

# Map document types to wiki subdirectories
_TYPE_DIRS = {
    "contract": "contracts",
    "statute": "statutes",
    "case_law": "cases",
    "memo": "memos",
    "regulation": "statutes",
    "filing": "cases",
    "other": "topics",
}


class WikiCompiler:
    """Orchestrates raw/ -> wiki/ compilation."""

    def __init__(self, config: LexWikiConfig):
        self.config = config
        self.raw_dir = config.raw_dir
        self.wiki_dir = config.wiki_dir

    def compile_all(self, full: bool = False) -> CompileStats:
        """Compile all raw files into wiki pages.

        If full=False, only compiles files that are new or modified since last compile.
        """
        stats = CompileStats()

        raw_files = sorted(self.raw_dir.glob("*.md"))
        if not raw_files:
            return stats

        for raw_path in raw_files:
            if not full and self._is_compiled(raw_path):
                continue

            pages = self.compile_file(raw_path)
            stats.pages_created += len(pages)

        if self.config.compile.rebuild_indexes_on_compile:
            idx_paths = self.rebuild_indexes()
            stats.indexes_rebuilt = len(idx_paths)

        bl_count = insert_backlinks(self.wiki_dir)
        stats.backlinks_inserted = bl_count

        return stats

    def compile_file(self, raw_path: Path) -> list[Path]:
        """Compile a single raw file into wiki page(s).

        Steps: classify -> chunk if needed -> generate page(s) -> write
        """
        content = self._read_raw_content(raw_path)
        if not content.strip():
            return []

        # Step 1: Classify
        meta = self._classify(content)

        # Step 2: Get known pages for backlinking
        known_pages = self._get_known_pages()

        # Step 3: Generate wiki page content
        if estimate_tokens(content) > self.config.compile.chunk_size:
            wiki_content = self._compile_chunked(content, meta, known_pages)
        else:
            wiki_content = self._compile_single(content, meta, known_pages)

        # Step 4: Clean up LLM output and write to wiki
        wiki_content = self._clean_llm_output(wiki_content)

        subdir = _TYPE_DIRS.get(meta.type, "topics")
        slug = _slugify(meta.title or raw_path.stem)
        out_dir = self.wiki_dir / subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{slug}.md"

        # Ensure the content has frontmatter; if LLM didn't include it, add it
        if not wiki_content.startswith("---"):
            wiki_content = self._build_frontmatter(meta, raw_path) + wiki_content

        out_path.write_text(wiki_content, encoding="utf-8")

        # Write a compile marker
        self._mark_compiled(raw_path)

        return [out_path]

    def rebuild_indexes(self) -> list[Path]:
        """Regenerate all index files from current wiki state."""
        manifest = self._build_pages_manifest()
        if not manifest.strip():
            return []

        indexes = {
            "_index.md": MASTER_INDEX_PROMPT,
            "_by_type.md": TYPE_INDEX_PROMPT,
            "_by_jurisdiction.md": JURISDICTION_INDEX_PROMPT,
            "_by_party.md": PARTY_INDEX_PROMPT,
            "_clause_library.md": CLAUSE_LIBRARY_PROMPT,
            "_precedent_map.md": PRECEDENT_MAP_PROMPT,
        }

        paths = []
        for filename, prompt_template in indexes.items():
            prompt = prompt_template.format(pages_manifest=manifest)
            content = self._complete_with_retry(prompt, INDEX_SYSTEM)
            out_path = self.wiki_dir / filename
            # Never overwrite a good index with empty/garbage output
            if len(content.strip()) < 50:
                import sys
                print(
                    f"Warning: Skipping {filename} — LLM returned insufficient content "
                    f"({len(content.strip())} chars). Keeping existing file.",
                    file=sys.stderr,
                )
                continue
            out_path.write_text(content, encoding="utf-8")
            paths.append(out_path)

        return paths

    def _classify(self, content: str) -> DocMeta:
        """Classify a document using the LLM.

        Sends both the beginning and end of the document to catch
        jurisdiction/governing law clauses that typically appear at the end.
        """
        excerpt_head = content[:3000]
        excerpt_tail = content[-2000:] if len(content) > 5000 else ""
        prompt = CLASSIFY_PROMPT.format(excerpt_head=excerpt_head, excerpt_tail=excerpt_tail)
        data = complete_structured(prompt, system=CLASSIFY_SYSTEM, config=self.config.llm)

        return DocMeta(
            type=data.get("type", "other"),
            title=data.get("title", "Untitled"),
            jurisdiction=data.get("jurisdiction", "unknown"),
            parties=data.get("parties", []),
            effective_date=data.get("effective_date"),
            subject_areas=data.get("subject_areas", []),
            confidence=data.get("confidence", 0.0),
        )

    def _compile_single(self, content: str, meta: DocMeta, known_pages: str) -> str:
        """Compile a document that fits in a single LLM call."""
        classification = json.dumps({
            "type": meta.type, "title": meta.title, "jurisdiction": meta.jurisdiction,
            "parties": meta.parties, "effective_date": meta.effective_date,
            "subject_areas": meta.subject_areas,
        }, indent=2)

        prompt = SUMMARIZE_PROMPT.format(
            known_pages=known_pages,
            classification=classification,
            content=content,
        )
        return complete(prompt, system=SUMMARIZE_SYSTEM, config=self.config.llm)

    def _compile_chunked(self, content: str, meta: DocMeta, known_pages: str) -> str:
        """Compile a large document by processing it in chunks."""
        chunks = chunk_text(
            content,
            max_tokens=self.config.compile.chunk_size,
            overlap_tokens=self.config.compile.chunk_overlap,
        )

        classification = json.dumps({
            "type": meta.type, "title": meta.title, "jurisdiction": meta.jurisdiction,
            "parties": meta.parties, "effective_date": meta.effective_date,
            "subject_areas": meta.subject_areas,
        }, indent=2)

        parts = []
        for i, chunk in enumerate(chunks, 1):
            prompt = SUMMARIZE_CHUNKED_PROMPT.format(
                chunk_num=i,
                total_chunks=len(chunks),
                classification=classification,
                known_pages=known_pages,
                content=chunk,
            )
            part = complete(prompt, system=SUMMARIZE_SYSTEM, config=self.config.llm)
            parts.append(part)

        # Combine with frontmatter
        frontmatter = self._build_frontmatter(meta, None)
        return frontmatter + "\n\n".join(parts)

    def _build_frontmatter(self, meta: DocMeta, raw_path: Path | None) -> str:
        """Build YAML frontmatter for a wiki page."""
        now = datetime.now(timezone.utc).isoformat()
        lines = [
            "---",
            f'type: "{meta.type}"',
            f'title: "{meta.title}"',
        ]
        if meta.parties:
            parties_str = ", ".join(f'"{p}"' for p in meta.parties)
            lines.append(f"parties: [{parties_str}]")
        lines.append(f'jurisdiction: "{meta.jurisdiction}"')
        if meta.effective_date:
            lines.append(f'effective_date: "{meta.effective_date}"')
        if meta.subject_areas:
            areas_str = ", ".join(f'"{a}"' for a in meta.subject_areas)
            lines.append(f"subject_areas: [{areas_str}]")
        lines.append(f'compiled_at: "{now}"')
        if raw_path:
            lines.append(f'source_raw: "{raw_path.name}"')
        lines.extend(["---", "", ""])
        return "\n".join(lines)

    @staticmethod
    def _clean_llm_output(text: str) -> str:
        """Strip markdown fences and duplicate frontmatter from LLM output.

        Some models wrap their entire response in ```markdown ... ``` fences,
        which results in the content being treated as a code block rather than
        rendered markdown. This strips that wrapper.
        """
        if not text:
            return ""
        stripped = text.strip()
        # Strip outer ```markdown ... ``` fence
        if stripped.startswith("```"):
            # Remove opening fence line
            first_newline = stripped.index("\n")
            stripped = stripped[first_newline + 1:]
            # Remove closing fence
            if stripped.rstrip().endswith("```"):
                stripped = stripped.rstrip()[:-3].rstrip()
        return stripped

    def _complete_with_retry(
        self, prompt: str, system: str, max_retries: int = 2, min_length: int = 50
    ) -> str:
        """Call the LLM with retry on garbage/truncated output.

        Retries if the response is shorter than min_length characters,
        which catches empty responses, truncated output like "I think I'll",
        and other model failures.
        """
        for attempt in range(max_retries + 1):
            content = complete(prompt, system=system, config=self.config.llm)
            content = self._clean_llm_output(content)
            if len(content.strip()) >= min_length:
                return content
            if attempt < max_retries:
                import sys
                print(
                    f"Warning: LLM returned short response ({len(content.strip())} chars), "
                    f"retrying ({attempt + 1}/{max_retries})...",
                    file=sys.stderr,
                )
        return content  # return whatever we got on last attempt

    def _get_known_pages(self) -> str:
        """Get a list of known wiki page names for backlinking."""
        pages = []
        for md_file in self.wiki_dir.rglob("*.md"):
            if md_file.name.startswith("_"):
                continue
            rel = md_file.relative_to(self.wiki_dir)
            pages.append(str(rel.with_suffix("")))
        return "\n".join(sorted(pages)) if pages else "(no existing pages)"

    def _build_pages_manifest(self, include_content: bool = True) -> str:
        """Build a manifest of all wiki pages for index generation.

        Includes frontmatter and the first ~500 chars of content so the LLM
        can extract entities, clauses, and relationships — not just metadata.
        """
        entries = []
        for md_file in sorted(self.wiki_dir.rglob("*.md")):
            if md_file.name.startswith("_"):
                continue
            try:
                text = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            # Extract frontmatter
            fm_match = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
            if fm_match:
                fm = fm_match.group(1)
                body = fm_match.group(2).strip()
            else:
                fm = ""
                body = text.strip()

            rel = md_file.relative_to(self.wiki_dir)
            entry = f"## [[{rel.stem}]] ({rel})\n{fm}\n"
            if include_content and body:
                # Include first ~500 chars of body for context
                snippet = body[:500]
                if len(body) > 500:
                    snippet += "\n[...]"
                entry += f"\nContent preview:\n{snippet}\n"
            entries.append(entry)

        return "\n".join(entries)

    def _read_raw_content(self, raw_path: Path) -> str:
        """Read a raw file, stripping the YAML frontmatter we added during ingest."""
        text = raw_path.read_text(encoding="utf-8")
        match = re.match(r"^---\n.*?\n---\n\n?(.*)", text, re.DOTALL)
        if match:
            return match.group(1)
        return text

    def _is_compiled(self, raw_path: Path) -> bool:
        """Check if a raw file has already been compiled (and hasn't changed since)."""
        marker = self._marker_path(raw_path)
        if not marker.exists():
            return False
        return marker.stat().st_mtime >= raw_path.stat().st_mtime

    def _mark_compiled(self, raw_path: Path):
        """Write a compile marker for a raw file."""
        marker = self._marker_path(raw_path)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(datetime.now(timezone.utc).isoformat())

    def _marker_path(self, raw_path: Path) -> Path:
        return self.raw_dir / ".compiled" / f"{raw_path.stem}.marker"


def _slugify(text: str) -> str:
    """Convert a title to a URL/filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-")
