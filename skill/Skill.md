---
name: "LexWiki Legal KB"
description: "Organize, query, and analyze legal documents using the LexWiki knowledge base tools"
---

# LexWiki Legal Knowledge Base

You have access to LexWiki tools for managing a legal knowledge base. Use them when the user asks about organizing, searching, analyzing, or reviewing legal documents.

## Available Tools

- **lexwiki_search** — Fast keyword search across all pages (no LLM call, instant, use this first for quick lookups)
- **lexwiki_query** — Answer complex legal questions using the knowledge base (LLM-powered, returns answers with citations)
- **lexwiki_ingest** — Add a legal document (PDF, DOCX, XLSX, PPTX, HTML, TXT) to the knowledge base
- **lexwiki_compile** — Compile raw documents into a structured wiki with backlinks, clause libraries, and indexes
- **lexwiki_lint** — Check for expired citations, inconsistent clauses, missing standard terms, broken links
- **lexwiki_read_page** — Read a specific wiki page
- **lexwiki_list_pages** — List all pages, optionally filtered by category

## Workflow

1. When the user provides legal documents, use **lexwiki_ingest** to add them
2. After ingesting, use **lexwiki_compile** to build the structured wiki
3. For quick lookups, use **lexwiki_search** first (free, instant, deterministic)
4. For complex questions, use **lexwiki_query** (LLM-powered, slower but synthesizes answers)
5. Periodically use **lexwiki_lint** to check for consistency issues
6. Use **lexwiki_read_page** to show the user specific wiki pages

## When to Use

- User says "organize my legal documents", "build a knowledge base", "analyze these contracts"
- User asks questions about their legal documents: "what are the termination provisions?", "which contracts have non-compete clauses?"
- User wants to compare clauses across contracts
- User asks about jurisdiction-specific requirements
- User wants to check document consistency or find expired references

## Tips

- Prefer **lexwiki_search** over **lexwiki_query** for simple lookups — it's free and instant
- Use **lexwiki_query** when the user needs a synthesized answer across multiple documents
- After compiling, suggest the user open the `vault/` directory in Obsidian for graph view and visual navigation
- The **_clause_library** index is especially useful for comparing similar clauses across contracts
- Use `--scope` with queries to narrow results (e.g. `scope="contracts"` or `scope="jurisdiction:UAE"`)
- Lint results with severity "error" should be addressed first
