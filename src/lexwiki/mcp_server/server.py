"""LexWiki MCP Server — exposes tools for IDE integration via FastMCP."""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("lexwiki", instructions="LLM-powered legal knowledge base. Use these tools to ingest legal documents, compile a structured wiki, query it, and lint for consistency.")


def _cfg():
    """Load config and ensure vault directories exist."""
    from lexwiki.config import load_config

    cfg = load_config()
    cfg.raw_dir.mkdir(parents=True, exist_ok=True)
    cfg.wiki_dir.mkdir(parents=True, exist_ok=True)
    return cfg


@mcp.tool()
def lexwiki_ingest(source_path: str) -> str:
    """Ingest a legal document (PDF, DOCX, XLSX, PPTX, HTML, TXT) into the raw knowledge base.

    Extracts text to markdown and stores in vault/raw/.
    """
    from lexwiki.extract.router import ingest_file

    cfg = _cfg()
    path = Path(source_path).resolve()

    if not path.exists():
        return f"Error: File not found: {source_path}"

    try:
        result = ingest_file(path, cfg.raw_dir)
        lines = [
            f"Ingested: {result.source.name}",
            f"Format: {result.format}",
            f"Words: {result.word_count}",
        ]
        if result.page_count:
            lines.append(f"Pages: {result.page_count}")
        lines.append(f"Output: {result.output}")
        lines.append("")
        lines.append("Run lexwiki_compile() to integrate into the wiki.")
        return "\n".join(lines)
    except ValueError as e:
        return f"Error: {e}"


@mcp.tool()
def lexwiki_compile(file_path: str | None = None, full: bool = False) -> str:
    """Compile raw documents into the structured legal wiki.

    Classifies documents, generates summaries with [[backlinks]],
    builds clause libraries, jurisdiction trackers, and indexes.
    """
    from lexwiki.compile.compiler import WikiCompiler

    cfg = _cfg()
    compiler = WikiCompiler(cfg)

    if file_path:
        pages = compiler.compile_file(Path(file_path).resolve())
        return f"Compiled {len(pages)} pages from {Path(file_path).name}."
    else:
        stats = compiler.compile_all(full=full)
        return (
            f"Compilation complete.\n"
            f"Pages created: {stats.pages_created}\n"
            f"Indexes rebuilt: {stats.indexes_rebuilt}\n"
            f"Backlinks inserted: {stats.backlinks_inserted}"
        )


@mcp.tool()
def lexwiki_query(question: str, scope: str | None = None) -> str:
    """Query the legal knowledge base using natural language.

    Uses the wiki's own indexes (no vector DB) to find relevant pages,
    then synthesizes an answer with [[page]] citations.
    """
    from lexwiki.query.engine import QueryEngine

    cfg = _cfg()
    engine = QueryEngine(cfg)
    return engine.query(question, scope=scope)


@mcp.tool()
def lexwiki_lint(file_path: str | None = None) -> str:
    """Check the legal wiki for consistency issues.

    Detects: expired statute citations, inconsistent clause language,
    missing standard terms, broken backlinks, stale summaries.
    """
    from lexwiki.lint.linter import WikiLinter

    cfg = _cfg()
    linter = WikiLinter(cfg)

    if file_path:
        issues = linter.lint_file(Path(file_path).resolve())
    else:
        issues = linter.lint_all()

    if not issues:
        return "No issues found."

    lines = [f"Found {len(issues)} issues:\n"]
    for issue in issues:
        lines.append(f"[{issue.severity.upper()}] {issue.category}")
        lines.append(f"  File: {issue.file}")
        lines.append(f"  {issue.message}")
        lines.append(f"  Suggestion: {issue.suggestion}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def lexwiki_read_page(page_name: str) -> str:
    """Read a specific wiki page by name.

    Args:
        page_name: Page name (e.g. "master-services-agreement") or relative path within wiki/.
    """
    cfg = _cfg()

    # Try direct path first
    direct = cfg.wiki_dir / page_name
    if direct.exists():
        return direct.read_text(encoding="utf-8")

    # Try with .md extension
    with_ext = cfg.wiki_dir / f"{page_name}.md"
    if with_ext.exists():
        return with_ext.read_text(encoding="utf-8")

    # Search by stem
    matches = list(cfg.wiki_dir.rglob(f"{page_name}.md"))
    if matches:
        return matches[0].read_text(encoding="utf-8")

    return f"Page not found: {page_name}"


@mcp.tool()
def lexwiki_list_pages(category: str | None = None) -> str:
    """List all pages in the wiki, optionally filtered by category.

    Args:
        category: Filter by type: "contracts", "statutes", "cases", "memos", "topics", "indexes"
    """
    cfg = _cfg()

    if category == "indexes":
        files = sorted(cfg.wiki_dir.glob("_*.md"))
    elif category:
        subdir = cfg.wiki_dir / category
        if not subdir.exists():
            return f"Category not found: {category}. Available: contracts, statutes, cases, memos, topics, indexes"
        files = sorted(subdir.rglob("*.md"))
    else:
        files = sorted(cfg.wiki_dir.rglob("*.md"))

    if not files:
        return "No pages found." + (f" (category: {category})" if category else "")

    lines = []
    for f in files:
        rel = f.relative_to(cfg.wiki_dir)
        lines.append(str(rel))
    return "\n".join(lines)


def serve():
    """Run the MCP server with stdio transport."""
    mcp.run(transport="stdio")
