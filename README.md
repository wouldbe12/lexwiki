# LexWiki

**Constantly-updated memory for your legal documents.** Drop in your legal knowledge: templates, actual client contracts, statutes, memos, even emails. The AI reads everything, organizes it, cross-references it, and keeps it updated. Any AI agent can use it.

LexWiki runs separately from your main AI agent and builds the library with an open-weights LLM you choose, through OpenRouter or fully on your own machine. Your agent reads the compiled library, never your raw documents.

## What Does It Do?

You have a folder of legal documents. LexWiki reads all of them and builds a structured library:

- **Clause library** — every liability cap, indemnification, and termination clause across all your contracts, side by side
- **Jurisdiction tracker** — documents grouped by governing law
- **Party index** — every entity mapped across every document
- **Precedent map** — which cases cite which statutes
- **Master index** — a table of contents for the whole library

When you add a new document and recompile, LexWiki reads it, figures out how it connects to everything else, and updates the library. Unchanged documents are skipped.

When you ask it to review itself, it finds expired statute citations, inconsistent clause language across contracts, and missing standard terms. The library keeps itself clean.

## How It Works Under the Hood

Everything lives in a **vault** — a folder on your computer (e.g. `~/my-legal-library/vault/`). Inside, there are two subfolders:

- `vault/raw/` — your original documents converted to readable text
- `vault/wiki/` — the compiled library with summaries, indexes, and cross-references

When you tell your agent to ingest a document, LexWiki extracts the text and saves it to `raw/`. When you tell it to compile, a separate LLM reads every document in `raw/`, classifies each one (contract, statute, memo, etc.), writes a structured summary, and links it to related documents. The result goes into `wiki/`.

**Your main agent (Claude, Cursor, etc.) only reads from `wiki/`.** It never sees your raw documents. The LLM that builds the library is a separate call — and you choose which model handles it.

### Setting Up an Open-Weights LLM via OpenRouter

LexWiki is built for open-weights models, so no proprietary AI company processes your documents. The easiest way to run them is [OpenRouter](https://openrouter.ai):

1. **Register** at [openrouter.ai](https://openrouter.ai) — it's free to sign up
2. **Add credits** — $5 is enough to process hundreds of documents
3. **Copy your API key** from the [Keys page](https://openrouter.ai/keys) (starts with `sk-or-`)
4. **Turn on Zero Data Retention** in your OpenRouter [privacy settings](https://openrouter.ai/settings/privacy), so your requests are only routed to providers that don't store prompts.
5. **Pick an open-weights model.** Good choices:
   - `deepseek/deepseek-v4.1-flash`: the default. Fast and very cheap, a good fit for compiling large libraries
   - `z-ai/glm-5.3-flash`: fast, strong at structured extraction
   - `qwen/qwen3.8-flash`: fast, good with non-English documents
   - `moonshotai/kimi-k3`: the strongest of the four, for deeper legal analysis at a higher price
6. **Set your environment variables:**

```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
export LEXWIKI_MODEL=deepseek/deepseek-v4.1-flash   # optional, this is the default
export LEXWIKI_VAULT=~/my-legal-library/vault
```

With this setup, your documents are processed by an open-weights model through OpenRouter's API. For maximum privacy, run a model entirely on your own machine with [Ollama](https://ollama.com) (for example `LEXWIKI_PROVIDER=ollama LEXWIKI_MODEL=qwen3.6`), and nothing leaves your computer.

## Quick Start for Lawyers

### If you use Claude Desktop (Chat or Cowork)

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) once (LexWiki runs through it), then download [`lexwiki.mcpb`](https://github.com/wouldbe12/lexwiki/releases/latest) from Releases
2. Double-click the file — Claude Desktop opens an install dialog
3. Enter your API key (get one free at [openrouter.ai](https://openrouter.ai))
4. Pick a folder where you want your library stored
5. Done. Switch to **Cowork** mode (the Tasks tab) and tell Claude:

- *"Ingest all the documents in ~/contracts/ and compile the library"*
- *"What are the termination provisions across all our agreements?"*
- *"Compare the liability caps in the MSA and NDA"*
- *"Review the library for inconsistencies"*

Works in both Chat and Cowork modes. In Cowork, Claude can handle multi-step tasks like ingesting a whole folder and compiling the library in one go.

### If you use Claude Code

Run this once in your terminal (requires [uv](https://docs.astral.sh/uv/getting-started/installation/)):

```bash
claude mcp add --transport stdio --scope user \
  -e OPENROUTER_API_KEY=sk-or-v1-your-key-here \
  -e LEXWIKI_VAULT=$HOME/my-legal-library/vault \
  lexwiki -- uvx --from git+https://github.com/wouldbe12/lexwiki lexwiki serve-mcp
```

Now Claude Code has access to your legal library in every project.

### If you use Cursor, Codex, Cline, or another MCP-compatible agent

Add this to your MCP settings (see table below for where the file lives):

```json
{
  "mcpServers": {
    "lexwiki": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/wouldbe12/lexwiki", "lexwiki", "serve-mcp"],
      "env": {
        "OPENROUTER_API_KEY": "sk-or-v1-your-key-here",
        "LEXWIKI_VAULT": "/path/to/your/vault"
      }
    }
  }
}
```

| Tool | Where to put the config |
|---|---|
| **Claude Desktop** | Download the `.mcpb` file above |
| **Claude Code** | Run the `claude mcp add` command above |
| **Cursor** | `.cursor/mcp.json` in your project folder |
| **Codex** | MCP config in project settings |
| **Cline / Roo Code** | VS Code settings > MCP Servers |

### Standalone (command line)

```bash
pip install git+https://github.com/wouldbe12/lexwiki

lexwiki init my-legal-library
cd my-legal-library
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
lexwiki ingest ~/contracts/
lexwiki compile
lexwiki query "What are the termination provisions?"
lexwiki search "liability cap"
```

## What Can Your Agent Do With It?

Once LexWiki is connected, your AI agent gets these tools:

| What you ask | What happens |
|---|---|
| *"Add this contract to the library"* | `lexwiki_ingest` — extracts text from PDF, Word, Excel, PowerPoint |
| *"Organize all the documents"* | `lexwiki_compile` — AI classifies, summarizes, cross-references everything |
| *"What are the key terms in the shareholders agreement?"* | `lexwiki_query` — reads the library, gives you an answer with citations |
| *"Find all mentions of indemnification"* | `lexwiki_search` — instant keyword search, no AI call needed |
| *"Check everything for problems"* | `lexwiki_lint` — finds expired citations, inconsistent clauses, missing terms |
| *"Show me the clause library"* | `lexwiki_read_page` — reads any page from the library |
| *"What documents do we have?"* | `lexwiki_list_pages` — lists everything by category |

## Supported Documents

PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx), HTML, Markdown, and plain text. Convert older .doc/.xls/.ppt files to the modern formats first.

## Privacy

LexWiki runs locally and stores everything in your vault folder. The only external call is to the model that builds the library, and you choose it:

- **OpenRouter** with an open-weights model (the default). Turn on Zero Data Retention in your OpenRouter settings.
- **Ollama**, running completely on your machine with zero external calls.

Your main AI agent (Claude, Cursor, etc.) only reads the compiled library, not your raw documents.

LexWiki only picks up `LEXWIKI_API_KEY` or `OPENROUTER_API_KEY` from your environment, never a generic provider key your agent happens to have set. No config file needed.

## Viewing the Library in Obsidian (Optional)

If you want a visual view of how your documents connect:

1. Install [Obsidian](https://obsidian.md) (free)
2. Open your `vault/` folder as a vault
3. Press Ctrl+G for the graph view — you'll see all your documents and how they link together
4. Click any document to read the AI-generated summary

This is optional. The library works perfectly without Obsidian — your AI agent accesses it directly.

## Built by Anylegal.ai

LexWiki is part of the [Anylegal.ai](https://anylegal.ai) ecosystem — AI-powered tools for legal teams. If you're using LexWiki and want to take it further, check out what we're building.

## License

AGPL-3.0 — see [LICENSE](LICENSE). [Privacy policy](PRIVACY.md).

Built by [Anylegal.ai](https://anylegal.ai).
