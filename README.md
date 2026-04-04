# LexWiki

**Constantly-updated memory for your legal documents.** Drop in your entire legal knowledge — up to 10,000 documents. Templates, actual client contracts, statutes, memos, even emails. The AI reads everything, organizes it, cross-references it, and keeps it updated. Any AI agent can use it.

LexWiki runs separately from your main AI agent and can be 100% private by using an open-source LLM. Your agent reads the compiled library, never your raw documents.

## What Does It Do?

You have a folder of legal documents. LexWiki reads all of them and builds a structured library:

- **Clause library** — every liability cap, indemnification, and termination clause across all your contracts, side by side
- **Jurisdiction tracker** — documents grouped by governing law
- **Party index** — every entity mapped across every document
- **Precedent map** — which cases cite which statutes
- **Master index** — a table of contents for the whole library

When you add a new document, LexWiki reads it, figures out how it connects to everything else, and updates the library automatically.

When you ask it to review itself, it finds expired statute citations, inconsistent clause language across contracts, and missing standard terms. The library keeps itself clean.

## How It Works Under the Hood

Everything lives in a **vault** — a folder on your computer (e.g. `~/my-legal-library/vault/`). Inside, there are two subfolders:

- `vault/raw/` — your original documents converted to readable text
- `vault/wiki/` — the compiled library with summaries, indexes, and cross-references

When you tell your agent to ingest a document, LexWiki extracts the text and saves it to `raw/`. When you tell it to compile, a separate LLM reads every document in `raw/`, classifies each one (contract, statute, memo, etc.), writes a structured summary, and links it to related documents. The result goes into `wiki/`.

**Your main agent (Claude, Cursor, etc.) only reads from `wiki/`.** It never sees your raw documents. The LLM that builds the library is a separate call — and you choose which model handles it.

### Setting Up a Private LLM via OpenRouter

If you don't want any proprietary AI company processing your documents, use an open-source model through [OpenRouter](https://openrouter.ai):

1. **Register** at [openrouter.ai](https://openrouter.ai) — it's free to sign up
2. **Add credits** — $5 is enough to process hundreds of documents
3. **Copy your API key** from the [Keys page](https://openrouter.ai/keys) (starts with `sk-or-`)
4. **Pick a powerful open-source model** for privacy. Good choices:
   - `stepfun/step-3.5-flash` — fast, cheap, tested with LexWiki
   - `moonshotai/kimi-k2.5` — strong reasoning, great for legal analysis
5. **Set your environment variables:**

```bash
export LEXWIKI_API_KEY=sk-or-v1-your-key-here
export LEXWIKI_MODEL=deepseek/deepseek-r1
export LEXWIKI_VAULT=~/my-legal-library/vault
```

With this setup, your documents are processed by an open-source model through OpenRouter's API. No data goes to Anthropic, OpenAI, or any other proprietary provider. For maximum privacy, you can also run a model entirely on your own machine using [Ollama](https://ollama.com) — zero external calls.

## Quick Start for Lawyers

### If you use Claude Desktop (Chat or Cowork)

1. Download [`lexwiki.mcpb`](https://github.com/wouldbe12/lexwiki/releases/latest) from Releases
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

Run this once in your terminal:

```bash
claude mcp add --transport stdio lexwiki -- uvx lexwiki serve-mcp
```

Set your API key:

```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
export LEXWIKI_VAULT=~/my-legal-library/vault
```

Now Claude Code has access to your legal library. All agent teammates in a Cowork session automatically get LexWiki tools too.

### If you use Cursor, Codex, Cline, or another MCP-compatible agent

Add this to your MCP settings (see table below for where the file lives):

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

| Tool | Where to put the config |
|---|---|
| **Claude Desktop** | Download the `.mcpb` file above |
| **Claude Code** | Run the `claude mcp add` command above |
| **Cursor** | `.cursor/mcp.json` in your project folder |
| **Codex** | MCP config in project settings |
| **Cline / Roo Code** | VS Code settings > MCP Servers |

### Standalone (command line)

```bash
pip install lexwiki

lexwiki init my-legal-library
cd my-legal-library
# Edit lexwiki.yaml with your API key
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

PDF, Word (.docx, .doc), Excel (.xlsx), PowerPoint (.pptx), HTML, and plain text.

## Privacy

**Your documents never leave your machine.** LexWiki runs locally. The only external call is to the AI model you choose — and you can choose a fully private one:

- **OpenRouter** — access hundreds of models, including private/open-source ones
- **Anthropic** (Claude) — direct API
- **OpenAI** (GPT) — direct API
- **Ollama** — runs completely on your machine, zero external calls

Your main AI agent (Claude, Cursor, etc.) only reads the compiled library, not your raw documents. You can use a different, private model to build the library.

LexWiki auto-detects your provider from the API key format. No config file needed.

## Viewing the Library in Obsidian (Optional)

If you want a visual view of how your documents connect:

1. Install [Obsidian](https://obsidian.md) (free)
2. Open your `vault/` folder as a vault
3. Press Ctrl+G for the graph view — you'll see all your documents and how they link together
4. Click any document to read the AI-generated summary

This is optional. The library works perfectly without Obsidian — your AI agent accesses it directly.

## Built by AnyLegal

LexWiki is part of the [anylegal.ai](https://anylegal.ai) ecosystem — AI-powered tools for legal teams. If you're using LexWiki and want to take it further, check out what we're building.

## License

AGPL-3.0 — see [LICENSE](LICENSE). [Privacy policy](PRIVACY.md).

Built by [AnyLegal](https://anylegal.ai).
