# LexWiki

**Constantly-updated memory for your legal documents.** Ingest contracts, statutes, and case law. The AI compiles a structured, cross-referenced library — queryable by any agent, lintable for consistency. No vector database required.

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

Download [`lexwiki.mcpb`](https://github.com/wouldbe12/lexwiki/releases/latest) from Releases and double-click to install. Claude Desktop will prompt for your API key and vault directory.

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

### Claude Desktop Skill

Download `skill/Skill.md` from this repo, zip it, and install via Claude Desktop:
1. Go to **Customize > Skills**
2. Upload the zip file
3. The skill teaches Claude when and how to use LexWiki tools

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

### Where to put the MCP config

| IDE | Config file location |
|---|---|
| **Claude Code** | Run `claude mcp add ...` or add `.mcp.json` to project root |
| **Claude Desktop** | Settings > Extensions (for .mcpb), or `~/.config/Claude/claude_desktop_config.json` |
| **Cursor** | `.cursor/mcp.json` in project root |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` |
| **Cline** | VS Code settings > Cline MCP Servers |

## Viewing in Obsidian

After compiling, open the `vault/` directory as an Obsidian vault:

1. Open Obsidian > **Open folder as vault**
2. Select your `vault/` directory
3. Enable **Graph view** (Ctrl+G) to see document relationships
4. Click any `[[backlink]]` to navigate between documents
5. Check `_index.md` for the master overview

Recommended Obsidian plugins:
- **Dataview** -- query your wiki with SQL-like syntax
- **Graph Analysis** -- find clusters and connections
- **Marp Slides** -- present wiki content as slideshows

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
