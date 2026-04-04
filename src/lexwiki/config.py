"""Configuration loading and project initialization."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class LLMConfig:
    provider: str = "anthropic"  # anthropic | openai | openrouter | ollama
    model: str = "claude-sonnet-4-20250514"
    api_key_env: str = "ANTHROPIC_API_KEY"
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.2


@dataclass
class CompileConfig:
    chunk_size: int = 12000
    chunk_overlap: int = 500
    rebuild_indexes_on_compile: bool = True


@dataclass
class LexWikiConfig:
    project_name: str = "LexWiki Project"
    vault_dir: Path = field(default_factory=lambda: Path("vault"))
    raw_dir: Path = field(default_factory=lambda: Path("vault/raw"))
    wiki_dir: Path = field(default_factory=lambda: Path("vault/wiki"))
    llm: LLMConfig = field(default_factory=LLMConfig)
    jurisdiction: str = "general"
    legal_domains: list[str] = field(
        default_factory=lambda: ["contracts", "statutes", "case_law", "memos"]
    )
    compile: CompileConfig = field(default_factory=CompileConfig)

    @property
    def root(self) -> Path:
        """Project root (parent of vault_dir)."""
        return self.vault_dir.parent


def _detect_provider_from_key(api_key: str) -> str:
    """Guess the provider from the API key format."""
    if api_key.startswith("sk-or-"):
        return "openrouter"
    if api_key.startswith("sk-ant-"):
        return "anthropic"
    if api_key.startswith("sk-"):
        return "openai"
    return "openrouter"  # safe default — accepts most models


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def load_config(path: Path | None = None) -> LexWikiConfig:
    """Load config from lexwiki.yaml, with env var overrides.

    Config file search order (when path is None):
        1. lexwiki.yaml in current directory
        2. lexwiki.yaml in LEXWIKI_VAULT parent directory
        3. lexwiki.yaml inside LEXWIKI_VAULT directory itself
        4. No file — use defaults + env vars

    Environment variables (for .mcpb / Docker / CI):
        LEXWIKI_VAULT       - vault directory path (absolute recommended)
        LEXWIKI_API_KEY     - LLM API key (auto-detects provider)
        LEXWIKI_PROVIDER    - LLM provider (anthropic|openai|openrouter|ollama)
        LEXWIKI_MODEL       - LLM model name
        LEXWIKI_BASE_URL    - Custom LLM endpoint

    Also checks common API key env vars as fallback:
        OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
    """
    if path is None:
        # Search for config file
        candidates = [Path("lexwiki.yaml")]
        vault_env = _env("LEXWIKI_VAULT")
        if vault_env:
            vault_path = Path(vault_env).resolve()
            candidates.append(vault_path.parent / "lexwiki.yaml")
            candidates.append(vault_path / "lexwiki.yaml")

        path = next((p for p in candidates if p.exists()), Path("lexwiki.yaml"))

    if path.exists():
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
    else:
        raw = {}

    # Resolve LLM config: env vars > yaml > defaults
    env_api_key = (
        _env("LEXWIKI_API_KEY")
        or _env("OPENROUTER_API_KEY")
        or _env("ANTHROPIC_API_KEY")
        or _env("OPENAI_API_KEY")
    )

    llm_raw = raw.get("llm", {})

    if env_api_key:
        provider = _env("LEXWIKI_PROVIDER") or _detect_provider_from_key(env_api_key)
        # Inject the key into the environment so llm/client.py can read it
        key_env_var = f"LEXWIKI_RESOLVED_API_KEY"
        os.environ[key_env_var] = env_api_key
        api_key_env = key_env_var
    else:
        provider = llm_raw.get("provider", "anthropic")
        api_key_env = llm_raw.get("api_key_env", "ANTHROPIC_API_KEY")

    llm = LLMConfig(
        provider=_env("LEXWIKI_PROVIDER") or provider,
        model=_env("LEXWIKI_MODEL") or llm_raw.get("model", "claude-sonnet-4-20250514"),
        api_key_env=api_key_env,
        base_url=_env("LEXWIKI_BASE_URL") or llm_raw.get("base_url"),
        max_tokens=llm_raw.get("max_tokens", 4096),
        temperature=llm_raw.get("temperature", 0.2),
    )

    compile_raw = raw.get("compile", {})
    compile_cfg = CompileConfig(
        chunk_size=compile_raw.get("chunk_size", 12000),
        chunk_overlap=compile_raw.get("chunk_overlap", 500),
        rebuild_indexes_on_compile=compile_raw.get("rebuild_indexes_on_compile", True),
    )

    # Vault dir: env var > yaml > default. Always resolve to absolute.
    # When LEXWIKI_VAULT is set, it takes full authority over paths.
    vault_env = _env("LEXWIKI_VAULT")
    if vault_env:
        vault_dir = Path(vault_env).resolve()
        raw_dir = vault_dir / "raw"
        wiki_dir = vault_dir / "wiki"
    else:
        vault_dir = Path(raw.get("vault_dir", "vault")).resolve()
        raw_dir = Path(raw.get("raw_dir", str(vault_dir / "raw"))).resolve()
        wiki_dir = Path(raw.get("wiki_dir", str(vault_dir / "wiki"))).resolve()
    return LexWikiConfig(
        project_name=raw.get("project_name", "LexWiki Project"),
        vault_dir=vault_dir,
        raw_dir=raw_dir,
        wiki_dir=wiki_dir,
        llm=llm,
        jurisdiction=raw.get("jurisdiction", "general"),
        legal_domains=raw.get("legal_domains", ["contracts", "statutes", "case_law", "memos"]),
        compile=compile_cfg,
    )


EXAMPLE_CONFIG = """\
# LexWiki Configuration
project_name: "My Legal KB"

# Directory layout (relative to project root)
vault_dir: vault
raw_dir: vault/raw
wiki_dir: vault/wiki

# LLM provider configuration
llm:
  provider: "anthropic"              # anthropic | openai | openrouter | ollama
  model: "claude-sonnet-4-20250514"
  api_key_env: "ANTHROPIC_API_KEY"   # env var name (not the key itself)
  base_url: null                     # override for custom endpoints
  max_tokens: 4096
  temperature: 0.2

  # OpenRouter example:
  # provider: "openrouter"
  # model: "anthropic/claude-sonnet-4-20250514"
  # api_key_env: "OPENROUTER_API_KEY"

  # Ollama example:
  # provider: "ollama"
  # model: "llama3"
  # base_url: "http://localhost:11434"

# Default jurisdiction context
jurisdiction: "general"

# Document types to expect
legal_domains:
  - contracts
  - statutes
  - case_law
  - memos

# Compilation settings
compile:
  chunk_size: 12000
  rebuild_indexes_on_compile: true
"""


GITIGNORE_TEMPLATE = """\
__pycache__/
*.py[cod]
.env
.env.local
"""


def init_project(directory: Path) -> Path:
    """Scaffold a new LexWiki project with dirs and example config."""
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)

    # Create vault structure
    (directory / "vault" / "raw").mkdir(parents=True, exist_ok=True)
    wiki = directory / "vault" / "wiki"
    wiki.mkdir(parents=True, exist_ok=True)
    for subdir in ["contracts", "statutes", "cases", "memos", "topics"]:
        (wiki / subdir).mkdir(exist_ok=True)

    # Write config
    config_path = directory / "lexwiki.yaml"
    if not config_path.exists():
        config_path.write_text(EXAMPLE_CONFIG)

    # Write .gitignore
    gi_path = directory / ".gitignore"
    if not gi_path.exists():
        gi_path.write_text(GITIGNORE_TEMPLATE)

    return directory
