# LexWiki

**LLM-powered legal knowledge base compiler.** Ingest legal documents, compile a structured Obsidian wiki, query with natural language, lint for consistency. No vector database required.

Inspired by [Karpathy's LLM Knowledge Bases](https://x.com/karpathy/status/2039805659525644595) pattern, built for legal.

## How It Works

```
Raw legal docs (PDF, DOCX, XLSX, PPTX, HTML, TXT)
    |
    v  lexwiki ingest
vault/raw/ (extracted markdown)
    |
    v  lexwiki compile
vault/wiki/ (structured Obsidian wiki with backlinks, indexes, clause libraries)
    |
    |-> lexwiki query "What are the termination provisions?"
    '-> lexwiki lint  (find expired citations, inconsistent clauses)
```

The LLM classifies documents, generates summaries, builds indexes, and maintains [[backlinks]]. You view the result in Obsidian. The wiki heals itself through linting.

## Install

### Claude Desktop (one-click)

Download `lexwiki.mcpb` from [Releases](https://github.com/wouldbe12/lexwiki/releases) and double-click to install. Claude Desktop will prompt for your API key and vault directory.

### Claude Code / Cowork

```bash
# One command — no pip install needed
claude mcp add --transport stdio lexwiki -- uvx lexwiki serve-mcp
```

Or for a project team, add `.mcp.json` to your repo:

```json
{
  "mcpServers": {
    "lexwiki": {
      "command": "uvx",
      "args": ["lexwiki", "serve-mcp"],
      "env": {
        "LEXWIKI_API_KEY": "${OPENROUTER_API_KEY}",
        "LEXWIKI_VAULT": "./vault"
      }
    }
  }
}
```

All cowork teammates automatically get LexWiki tools.

### Cursor / Windsurf / Cline

Add to your MCP settings:

```json
{
  "mcpServers": {
    "lexwiki": {
      "command": "uvx",
      "args": ["lexwiki", "serve-mcp"],
      "env": {
        "LEXWIKI_API_KEY": "your-api-key-here",
        "LEXWIKI_VAULT": "/path/to/your/vault"
      }
    }
  }
}
```

### pip (standalone CLI)

```bash
pip install lexwiki

lexwiki init my-legal-kb
cd my-legal-kb
# Edit lexwiki.yaml with your LLM provider
lexwiki ingest ~/contracts/
lexwiki compile
lexwiki query "What are the termination provisions?"
lexwiki lint
```

## Environment Variables

LexWiki works without a config file via environment variables:

| Variable | Description |
|---|---|
| `LEXWIKI_API_KEY` | LLM API key (auto-detects provider from key format) |
| `LEXWIKI_VAULT` | Path to vault directory |
| `LEXWIKI_PROVIDER` | `openrouter`, `anthropic`, `openai`, or `ollama` |
| `LEXWIKI_MODEL` | Model name (e.g. `anthropic/claude-sonnet-4-20250514`) |
| `LEXWIKI_BASE_URL` | Custom LLM endpoint |

Also reads `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` as fallbacks.

## CLI Commands

```bash
lexwiki init [dir]              # scaffold project
lexwiki ingest <file-or-dir>    # extract docs to raw markdown
lexwiki compile [--full]        # compile wiki with indexes + backlinks
lexwiki query "question"        # natural language Q&A
lexwiki lint                    # consistency checks
lexwiki serve-mcp               # start MCP server (stdio)
```

## MCP Tools

| Tool | Description |
|---|---|
| `lexwiki_ingest` | Ingest PDF, DOCX, XLSX, PPTX, HTML, TXT |
| `lexwiki_compile` | Compile wiki with backlinks + indexes |
| `lexwiki_query` | Natural language Q&A with citations |
| `lexwiki_lint` | Find expired citations, inconsistent clauses |
| `lexwiki_read_page` | Read a specific wiki page |
| `lexwiki_list_pages` | List pages by category |

## Supported Document Formats

| Format | Library |
|---|---|
| PDF | pymupdf4llm |
| DOCX | mammoth |
| XLSX | openpyxl |
| PPTX | python-pptx |
| HTML | trafilatura |
| TXT/MD | passthrough |

## What Gets Compiled

| Raw Input | Wiki Output |
|---|---|
| Contracts | Summaries with key terms, obligations by party, clause extraction |
| Statutes | Key provisions with section numbers, effective dates |
| Case Law | Holdings, ratio decidendi, cited authorities |
| Memos | Recommendations, referenced documents |
| Spreadsheets | Structured data tables with context |
| Presentations | Slide-by-slide analysis with notes |

Auto-generated index pages:
- `_index.md` -- master index (the retrieval layer)
- `_by_type.md` -- grouped by document type
- `_by_jurisdiction.md` -- grouped by jurisdiction
- `_by_party.md` -- all parties across documents
- `_clause_library.md` -- standard clauses across contracts
- `_precedent_map.md` -- case/statute citation graph

## LLM Provider Configuration

Via `lexwiki.yaml` or environment variables. Supports:

- **OpenRouter** (any model) -- `LEXWIKI_API_KEY=sk-or-...`
- **Anthropic** -- `LEXWIKI_API_KEY=sk-ant-...`
- **OpenAI** -- `LEXWIKI_API_KEY=sk-...`
- **Ollama** (local) -- `LEXWIKI_PROVIDER=ollama LEXWIKI_MODEL=llama3`

Auto-detects provider from API key format. No config file needed.

## Why No Vector Database?

Following the [Karpathy approach](https://x.com/karpathy/status/2039805659525644595): at the scale of a personal or small-firm legal knowledge base (100-10,000 documents), LLM-maintained markdown indexes outperform vector similarity search.

| | Vector DB / RAG | LexWiki |
|---|---|---|
| Data format | Opaque vectors | Human-readable markdown |
| Logic | Semantic similarity | Explicit connections (backlinks, indexes) |
| Auditability | Low | High (every claim traceable to source) |
| Compounding | Static re-indexing | Self-healing (lint + recompile) |
| Scale | Millions of docs | 100-10,000 high-signal docs |

For legal work, auditability is non-negotiable. Every claim in the wiki traces back to a specific source document.

## Privacy

LexWiki runs entirely on your machine. Documents are never sent to AnyLegal servers. The only external communication is with the LLM provider you configure. See [PRIVACY.md](PRIVACY.md).

## License

AGPL-3.0 -- see [LICENSE](LICENSE).

Built by [AnyLegal](https://anylegal.ai).
