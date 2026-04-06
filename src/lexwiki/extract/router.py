"""Route documents to the appropriate extractor and write to raw/."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from lexwiki.types import IngestResult

_EXTRACTORS = {
    ".pdf": "lexwiki.extract.pdf:extract_pdf",
    ".docx": "lexwiki.extract.docx:extract_docx",
    ".xlsx": "lexwiki.extract.xlsx:extract_xlsx",
    ".xls": "lexwiki.extract.xlsx:extract_xlsx",
    ".pptx": "lexwiki.extract.pptx:extract_pptx",
    ".ppt": "lexwiki.extract.pptx:extract_pptx",
    ".html": "lexwiki.extract.html:extract_html",
    ".htm": "lexwiki.extract.html:extract_html",
    ".txt": "lexwiki.extract.plain:extract_plain",
    ".md": "lexwiki.extract.plain:extract_plain",
}

SUPPORTED_EXTENSIONS = set(_EXTRACTORS.keys())


def _load_extractor(dotted_path: str):
    """Dynamically import an extractor function."""
    module_path, func_name = dotted_path.rsplit(":", 1)
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def ingest_file(source: Path, raw_dir: Path) -> IngestResult:
    """Extract a document to markdown and write to raw_dir.

    The output filename is the source stem + .md, with YAML frontmatter.
    """
    source = source.resolve()
    ext = source.suffix.lower()

    if ext not in _EXTRACTORS:
        raise ValueError(
            f"Unsupported format: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    extractor = _load_extractor(_EXTRACTORS[ext])
    content, page_count = extractor(source)

    word_count = len(content.split())

    # Build output with YAML frontmatter
    now = datetime.now(timezone.utc).isoformat()
    frontmatter = (
        f"---\n"
        f"source: \"{source}\"\n"
        f"ingested_at: \"{now}\"\n"
        f"format: \"{ext.lstrip('.')}\"\n"
    )
    if page_count is not None:
        frontmatter += f"pages: {page_count}\n"
    frontmatter += f"word_count: {word_count}\n---\n\n"

    output_path = raw_dir / f"{source.stem}.md"

    # Handle name collisions
    counter = 1
    while output_path.exists():
        output_path = raw_dir / f"{source.stem}_{counter}.md"
        counter += 1

    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(frontmatter + content, encoding="utf-8")

    return IngestResult(
        source=source,
        output=output_path,
        format=ext.lstrip("."),
        word_count=word_count,
        page_count=page_count,
    )


def ingest_directory(
    source_dir: Path, raw_dir: Path, on_error: str = "warn"
) -> list[IngestResult]:
    """Ingest all supported files from a directory (non-recursive).

    on_error: "warn" to print and skip, "raise" to stop on first error.
    """
    results = []
    for path in sorted(source_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                results.append(ingest_file(path, raw_dir))
            except Exception as e:
                if on_error == "raise":
                    raise
                import sys
                print(f"Warning: Failed to ingest {path.name}: {e}", file=sys.stderr)
    return results
