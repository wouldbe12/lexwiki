"""LexWiki CLI — all commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="lexwiki",
    help="LLM-powered legal knowledge base compiler.",
    no_args_is_help=True,
)
console = Console()


def _load_config():
    from lexwiki.config import load_config

    return load_config()


@app.command()
def init(
    directory: Path = typer.Argument(
        Path("."), help="Directory to initialize the project in."
    ),
):
    """Initialize a new LexWiki project with vault structure and example config."""
    from lexwiki.config import init_project

    path = init_project(directory)
    console.print(f"[green]Initialized LexWiki project at {path}[/green]")
    console.print("  vault/raw/   — drop your legal documents here")
    console.print("  vault/wiki/  — compiled wiki will appear here")
    console.print("  lexwiki.yaml — configure your LLM provider")
    console.print()
    console.print("Next: [bold]lexwiki ingest <file-or-directory>[/bold]")


@app.command()
def ingest(
    source: Path = typer.Argument(..., help="File or directory to ingest."),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recurse into subdirectories."),
):
    """Extract legal documents (PDF, DOCX, HTML, TXT) to raw markdown."""
    from lexwiki.extract.router import ingest_file, ingest_directory, SUPPORTED_EXTENSIONS

    cfg = _load_config()
    source = source.resolve()

    if not source.exists():
        console.print(f"[red]Not found: {source}[/red]")
        raise typer.Exit(1)

    if source.is_file():
        try:
            result = ingest_file(source, cfg.raw_dir)
            console.print(f"[green]Ingested:[/green] {result.source.name}")
            console.print(f"  Format: {result.format} | Words: {result.word_count}", end="")
            if result.page_count:
                console.print(f" | Pages: {result.page_count}")
            else:
                console.print()
            console.print(f"  Output: {result.output}")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)
    else:
        results = ingest_directory(source, cfg.raw_dir)
        if not results:
            console.print(f"[yellow]No supported files found in {source}[/yellow]")
            console.print(f"  Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
            raise typer.Exit(1)

        table = Table(title=f"Ingested {len(results)} files")
        table.add_column("File", style="cyan")
        table.add_column("Format")
        table.add_column("Words", justify="right")
        for r in results:
            table.add_row(r.source.name, r.format, str(r.word_count))
        console.print(table)

    console.print()
    console.print("Next: [bold]lexwiki compile[/bold]")


@app.command()
def compile(
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Compile a single raw file."),
    full: bool = typer.Option(False, "--full", help="Full recompile of all raw files."),
    indexes_only: bool = typer.Option(False, "--indexes", help="Only rebuild index pages."),
):
    """Compile raw markdown into a structured wiki with backlinks and indexes."""
    from lexwiki.compile.compiler import WikiCompiler

    cfg = _load_config()
    compiler = WikiCompiler(cfg)

    with console.status("[bold blue]Compiling wiki..."):
        if indexes_only:
            paths = compiler.rebuild_indexes()
            console.print(f"[green]Rebuilt {len(paths)} index pages.[/green]")
        elif file:
            pages = compiler.compile_file(file.resolve())
            console.print(f"[green]Compiled {len(pages)} pages from {file.name}.[/green]")
        else:
            stats = compiler.compile_all(full=full)
            console.print(f"[green]Compilation complete.[/green]")
            console.print(f"  Pages created: {stats.pages_created}")
            console.print(f"  Pages updated: {stats.pages_updated}")
            console.print(f"  Indexes rebuilt: {stats.indexes_rebuilt}")
            console.print(f"  Backlinks inserted: {stats.backlinks_inserted}")

    console.print()
    console.print("View in Obsidian: open [bold]vault/[/bold] as a vault.")


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask the knowledge base."),
    scope: Optional[str] = typer.Option(None, help="Scope filter, e.g. 'contracts', 'jurisdiction:UAE'."),
    save: bool = typer.Option(False, "--save", "-s", help="Save the answer as a wiki page."),
):
    """Query the legal knowledge base using natural language."""
    from lexwiki.query.engine import QueryEngine

    cfg = _load_config()
    engine = QueryEngine(cfg)

    with console.status("[bold blue]Researching..."):
        answer = engine.query(question, scope=scope)

    console.print()
    console.print(answer)

    if save:
        import re
        slug = re.sub(r"[^\w\s-]", "", question.lower())
        slug = re.sub(r"[\s]+", "-", slug)[:60]
        out_path = cfg.wiki_dir / "queries" / f"{slug}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(f"# {question}\n\n{answer}\n", encoding="utf-8")
        console.print(f"\n[green]Saved to {out_path}[/green]")


@app.command()
def search(
    query_text: str = typer.Argument(..., help="Keywords to search for."),
    top_k: int = typer.Option(10, "--top", "-k", help="Number of results."),
):
    """Keyword search across wiki pages (BM25 ranking, no LLM needed)."""
    from lexwiki.query.search import search_pages

    cfg = _load_config()
    results = search_pages(query_text, cfg.wiki_dir, top_k=top_k)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Search: {query_text}")
    table.add_column("Page", style="cyan")
    table.add_column("Score", justify="right")
    for path, score in results:
        rel = path.relative_to(cfg.wiki_dir)
        table.add_row(str(rel), f"{score:.2f}")
    console.print(table)


@app.command()
def lint(
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Lint a single wiki page."),
    severity: str = typer.Option("warning", help="Minimum severity: info, warning, error."),
):
    """Check the wiki for legal consistency issues and stale content."""
    from lexwiki.lint.linter import WikiLinter

    cfg = _load_config()
    linter = WikiLinter(cfg)

    with console.status("[bold blue]Linting wiki..."):
        if file:
            issues = linter.lint_file(file.resolve())
        else:
            issues = linter.lint_all()

    severity_order = {"info": 0, "warning": 1, "error": 2}
    min_sev = severity_order.get(severity, 1)
    issues = [i for i in issues if severity_order.get(i.severity, 0) >= min_sev]

    if not issues:
        console.print("[green]No issues found.[/green]")
        return

    table = Table(title=f"{len(issues)} issues found")
    table.add_column("Sev", style="bold")
    table.add_column("Category")
    table.add_column("File", style="cyan")
    table.add_column("Message")
    table.add_column("Suggestion", style="dim")

    sev_colors = {"error": "red", "warning": "yellow", "info": "blue"}
    for issue in sorted(issues, key=lambda i: -severity_order.get(i.severity, 0)):
        color = sev_colors.get(issue.severity, "white")
        table.add_row(
            f"[{color}]{issue.severity}[/{color}]",
            issue.category,
            issue.file,
            issue.message,
            issue.suggestion,
        )
    console.print(table)


@app.command(name="serve-mcp")
def serve_mcp():
    """Start the MCP server (stdio transport) for IDE integration."""
    from lexwiki.mcp_server.server import serve

    serve()


if __name__ == "__main__":
    app()
