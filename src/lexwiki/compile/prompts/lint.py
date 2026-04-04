"""Prompt templates for wiki linting."""

LINT_SYSTEM = """\
You are a legal consistency checker. You identify issues in a legal knowledge base \
that could indicate errors, staleness, or inconsistencies. Respond only with valid JSON."""

LINT_PROMPT = """\
Review these wiki pages for legal consistency issues.

Check for:
1. EXPIRED CITATIONS: Statute references that may be outdated (check effective dates, known repeals)
2. INCONSISTENT CLAUSES: Same clause type with contradictory language across contracts
3. MISSING STANDARD TERMS: Contracts missing commonly expected clauses for their type
4. CROSS-REFERENCE ERRORS: References to provisions or sections that don't match the source
5. AMBIGUOUS TERMS: Legal terms used inconsistently across documents

Pages to check:
---
{pages_content}
---

{clause_library_section}

Respond with a JSON array of issues (empty array if no issues found):
[{{
  "severity": "error" | "warning" | "info",
  "category": "expired_citation" | "inconsistent_clause" | "missing_term" | "cross_reference_error" | "ambiguous_term",
  "file": "relative/path/to/file.md",
  "line": null,
  "message": "Description of the issue",
  "suggestion": "How to fix it"
}}]
"""
