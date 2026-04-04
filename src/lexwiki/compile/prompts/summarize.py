"""Prompt templates for wiki page generation."""

SUMMARIZE_SYSTEM = """\
You are a legal knowledge base compiler. You convert raw legal documents into \
structured, interlinked Obsidian wiki pages.

Formatting rules:
- Start with YAML frontmatter (type, title, parties, jurisdiction, effective_date, source_raw, subject_areas)
- Write a one-paragraph Summary section
- Extract key terms as a markdown table where applicable
- Identify obligations by party for contracts
- Extract notable clauses with their own subsections
- Insert [[backlinks]] to other known pages where relevant (use the page filename without extension)
- Be precise and factual. Never invent terms not in the source document.
- For statutes: list key provisions with section numbers
- For case law: state the holding, ratio decidendi, and cited authorities
- For memos: summarize recommendations and referenced documents
- For regulations: list requirements and compliance obligations
"""

SUMMARIZE_PROMPT = """\
Convert this raw legal document into a structured wiki page.

Known pages in the wiki (use [[page-name]] to create backlinks):
{known_pages}

Document classification:
{classification}

Full document content:
---
{content}
---

Generate the complete wiki page in markdown, starting with the YAML frontmatter block.
"""

SUMMARIZE_CHUNKED_PROMPT = """\
You are compiling part {chunk_num} of {total_chunks} of a large legal document into wiki content.

Document classification:
{classification}

Known pages in the wiki:
{known_pages}

Document chunk ({chunk_num}/{total_chunks}):
---
{content}
---

Generate the wiki content for this section. Do NOT include YAML frontmatter (it will be added separately). \
Use [[backlinks]] where relevant. Be precise and factual.
"""
