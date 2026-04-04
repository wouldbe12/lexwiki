# LexWiki Privacy Policy

**Last updated:** April 4, 2026

## Overview

LexWiki is an open-source tool that runs entirely on your local machine. Your legal documents never leave your computer unless you explicitly configure an external LLM provider.

## Data Processing

- **Local storage:** All documents, the compiled wiki, and indexes are stored locally in the vault directory you specify. LexWiki does not transmit your documents to any server operated by AnyLegal.

- **LLM API calls:** When you use compile, query, or lint commands, document content is sent to the LLM provider you configure (e.g., Anthropic, OpenAI, OpenRouter, or a local Ollama instance). LexWiki does not proxy, log, or store these API calls. Review your LLM provider's privacy policy for how they handle data sent to their API.

- **No telemetry:** LexWiki does not collect usage analytics, crash reports, or any telemetry data.

- **No accounts:** LexWiki does not require user accounts or registration.

## API Keys

API keys are stored locally:
- In `lexwiki.yaml` (as an environment variable name reference, not the key itself)
- In Claude Desktop's OS keychain (when installed as a .mcpb extension)
- In environment variables (when used via CLI or MCP)

LexWiki never transmits API keys to AnyLegal or any third party.

## Third-Party Services

The only external services LexWiki communicates with are the LLM API providers you configure. These are:

| Provider | Privacy Policy |
|---|---|
| Anthropic | https://www.anthropic.com/privacy |
| OpenAI | https://openai.com/privacy |
| OpenRouter | https://openrouter.ai/privacy |
| Ollama | Local only, no external communication |

## Open Source

LexWiki is open source under the AGPL-3.0 license. You can audit the complete source code at https://github.com/wouldbe12/lexwiki to verify these privacy claims.

## Contact

For privacy questions: hello@anylegal.ai

AnyLegal  
https://anylegal.ai
