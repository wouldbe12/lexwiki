"""Tests for configuration loading and project initialization."""

from pathlib import Path
from lexwiki.config import load_config, init_project, LexWikiConfig


def test_default_config():
    """Loading config with no file returns defaults."""
    cfg = load_config(Path("/nonexistent/lexwiki.yaml"))
    assert cfg.project_name == "LexWiki Project"
    assert cfg.llm.provider == "anthropic"
    assert cfg.llm.model == "claude-sonnet-4-20250514"


def test_load_config_from_yaml(tmp_path):
    """Load config from a YAML file."""
    cfg_file = tmp_path / "lexwiki.yaml"
    cfg_file.write_text("""\
project_name: "Test Project"
llm:
  provider: "openrouter"
  model: "anthropic/claude-sonnet-4-20250514"
  api_key_env: "OPENROUTER_API_KEY"
jurisdiction: "UAE"
""")
    cfg = load_config(cfg_file)
    assert cfg.project_name == "Test Project"
    assert cfg.llm.provider == "openrouter"
    assert cfg.jurisdiction == "UAE"


def test_init_project(tmp_path):
    """Project initialization creates expected structure."""
    project_dir = tmp_path / "my-kb"
    init_project(project_dir)

    assert (project_dir / "vault" / "raw").is_dir()
    assert (project_dir / "vault" / "wiki" / "contracts").is_dir()
    assert (project_dir / "vault" / "wiki" / "statutes").is_dir()
    assert (project_dir / "vault" / "wiki" / "cases").is_dir()
    assert (project_dir / "vault" / "wiki" / "memos").is_dir()
    assert (project_dir / "vault" / "wiki" / "topics").is_dir()
    assert (project_dir / "lexwiki.yaml").exists()
    assert (project_dir / ".gitignore").exists()
