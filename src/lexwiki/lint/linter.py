"""WikiLinter — check the wiki for consistency issues."""

from __future__ import annotations

import re
from pathlib import Path

from lexwiki.compile.prompts.lint import LINT_PROMPT, LINT_SYSTEM
from lexwiki.config import LexWikiConfig
from lexwiki.llm.client import complete_structured
from lexwiki.llm.tokens import estimate_tokens, truncate_to_tokens
from lexwiki.types import LintIssue


class WikiLinter:
    """Legal-specific linting of the compiled wiki."""

    def __init__(self, config: LexWikiConfig):
        self.config = config
        self.wiki_dir = config.wiki_dir
        self.raw_dir = config.raw_dir

    def lint_all(self) -> list[LintIssue]:
        """Run all lint checks across the entire wiki."""
        issues: list[LintIssue] = []

        # Fast checks (no LLM)
        issues.extend(self._check_broken_backlinks())
        issues.extend(self._check_stale_pages())

        # LLM-based checks (batch pages to fit context)
        issues.extend(self._check_legal_consistency())

        return issues

    def lint_file(self, wiki_path: Path) -> list[LintIssue]:
        """Lint a single wiki page."""
        issues: list[LintIssue] = []

        # Check backlinks in this file
        issues.extend(self._check_file_backlinks(wiki_path))

        # Check staleness
        issues.extend(self._check_file_staleness(wiki_path))

        # LLM check on single file
        try:
            content = wiki_path.read_text(encoding="utf-8")
            rel = wiki_path.relative_to(self.wiki_dir)
            issues.extend(self._llm_lint(f"## {rel}\n{content}"))
        except (OSError, UnicodeDecodeError):
            pass

        return issues

    def _check_broken_backlinks(self) -> list[LintIssue]:
        """Pure filesystem check: do all [[links]] resolve to actual files?"""
        issues = []
        all_stems = {
            p.stem.lower()
            for p in self.wiki_dir.rglob("*.md")
        }

        for md_file in self.wiki_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            rel = md_file.relative_to(self.wiki_dir)
            # Find all [[links]]
            for match in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content):
                link_target = match.group(1).strip()
                if link_target.lower() not in all_stems:
                    issues.append(LintIssue(
                        severity="warning",
                        category="broken_backlink",
                        file=str(rel),
                        line=None,
                        message=f"Broken backlink: [[{link_target}]] does not resolve to any wiki page.",
                        suggestion=f"Remove the link or create a page named '{link_target}'.",
                    ))

        return issues

    def _check_file_backlinks(self, wiki_path: Path) -> list[LintIssue]:
        """Check backlinks in a single file."""
        issues = []
        all_stems = {p.stem.lower() for p in self.wiki_dir.rglob("*.md")}

        try:
            content = wiki_path.read_text(encoding="utf-8")
            rel = wiki_path.relative_to(self.wiki_dir)
        except (OSError, UnicodeDecodeError, ValueError):
            return issues

        for match in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content):
            link_target = match.group(1).strip()
            if link_target.lower() not in all_stems:
                issues.append(LintIssue(
                    severity="warning",
                    category="broken_backlink",
                    file=str(rel),
                    line=None,
                    message=f"Broken backlink: [[{link_target}]]",
                    suggestion=f"Remove the link or create '{link_target}'.",
                ))

        return issues

    def _check_stale_pages(self) -> list[LintIssue]:
        """Flag wiki pages whose source raw file was modified after compilation."""
        issues = []
        compiled_dir = self.raw_dir / ".compiled"

        for md_file in self.wiki_dir.rglob("*.md"):
            if md_file.name.startswith("_"):
                continue

            # Try to find the source raw file via frontmatter
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not fm_match:
                continue

            source_raw = None
            for line in fm_match.group(1).split("\n"):
                if line.startswith("source_raw:"):
                    source_raw = line.split(":", 1)[1].strip().strip("\"'")
                    break

            if not source_raw:
                continue

            raw_path = self.raw_dir / source_raw
            if not raw_path.exists():
                continue

            marker = compiled_dir / f"{raw_path.stem}.marker"
            if marker.exists() and raw_path.stat().st_mtime > marker.stat().st_mtime:
                rel = md_file.relative_to(self.wiki_dir)
                issues.append(LintIssue(
                    severity="info",
                    category="stale_page",
                    file=str(rel),
                    line=None,
                    message=f"Source file '{source_raw}' was modified after last compilation.",
                    suggestion="Run `lexwiki compile` to update this page.",
                ))

        return issues

    def _check_file_staleness(self, wiki_path: Path) -> list[LintIssue]:
        """Check staleness for a single file."""
        issues = []
        try:
            content = wiki_path.read_text(encoding="utf-8")
            rel = wiki_path.relative_to(self.wiki_dir)
        except (OSError, UnicodeDecodeError, ValueError):
            return issues

        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not fm_match:
            return issues

        for line in fm_match.group(1).split("\n"):
            if line.startswith("source_raw:"):
                source_raw = line.split(":", 1)[1].strip().strip("\"'")
                raw_path = self.raw_dir / source_raw
                compiled_dir = self.raw_dir / ".compiled"
                marker = compiled_dir / f"{raw_path.stem}.marker"
                if raw_path.exists() and marker.exists():
                    if raw_path.stat().st_mtime > marker.stat().st_mtime:
                        issues.append(LintIssue(
                            severity="info",
                            category="stale_page",
                            file=str(rel),
                            line=None,
                            message=f"Source '{source_raw}' modified after compilation.",
                            suggestion="Run `lexwiki compile` to update.",
                        ))
                break

        return issues

    def _check_legal_consistency(self) -> list[LintIssue]:
        """Use LLM to check for legal consistency issues across wiki pages."""
        pages_content = []
        total_tokens = 0
        max_tokens = self.config.llm.max_tokens * 6

        for md_file in sorted(self.wiki_dir.rglob("*.md")):
            if md_file.name.startswith("_"):
                continue
            try:
                text = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            rel = md_file.relative_to(self.wiki_dir)
            entry = f"## {rel}\n{text}"
            tokens = estimate_tokens(entry)

            if total_tokens + tokens > max_tokens:
                break

            pages_content.append(entry)
            total_tokens += tokens

        if not pages_content:
            return []

        return self._llm_lint("\n\n---\n\n".join(pages_content))

    def _llm_lint(self, pages_content: str) -> list[LintIssue]:
        """Run LLM lint on a block of page content."""
        clause_lib_path = self.wiki_dir / "_clause_library.md"
        if clause_lib_path.exists():
            clause_lib = clause_lib_path.read_text(encoding="utf-8")
            clause_section = f"Clause library for comparison:\n---\n{truncate_to_tokens(clause_lib, 4000)}\n---"
        else:
            clause_section = ""

        prompt = LINT_PROMPT.format(
            pages_content=truncate_to_tokens(pages_content, 16000),
            clause_library_section=clause_section,
        )

        try:
            data = complete_structured(prompt, system=LINT_SYSTEM, config=self.config.llm)
            if not isinstance(data, list):
                return []

            return [
                LintIssue(
                    severity=item.get("severity", "info"),
                    category=item.get("category", "other"),
                    file=item.get("file", "unknown"),
                    line=item.get("line"),
                    message=item.get("message", ""),
                    suggestion=item.get("suggestion", ""),
                )
                for item in data
            ]
        except (ValueError, KeyError):
            return []
