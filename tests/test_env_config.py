"""Test that LEXWIKI_VAULT env var resolves paths correctly from any CWD."""

import os


def test_vault_env_overrides_yaml(tmp_path):
    """When LEXWIKI_VAULT is set, paths resolve to it regardless of CWD or yaml."""
    # Create a vault structure
    vault = tmp_path / "my-vault"
    (vault / "raw").mkdir(parents=True)
    wiki = vault / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "_index.md").write_text("# Index")

    # Also create a lexwiki.yaml in vault parent with DIFFERENT relative paths
    (tmp_path / "lexwiki.yaml").write_text(
        "vault_dir: some-other-vault\nraw_dir: some-other-vault/raw\n"
    )

    os.environ["LEXWIKI_VAULT"] = str(vault)
    try:
        from lexwiki.config import load_config

        cfg = load_config()
        assert cfg.vault_dir == vault
        assert cfg.raw_dir == vault / "raw"
        assert cfg.wiki_dir == vault / "wiki"
        assert cfg.wiki_dir.exists()
        assert (cfg.wiki_dir / "_index.md").exists()
    finally:
        del os.environ["LEXWIKI_VAULT"]


def test_vault_env_absolute_from_any_cwd(tmp_path, monkeypatch):
    """LEXWIKI_VAULT works even when CWD is completely unrelated."""
    vault = tmp_path / "legal-kb" / "vault"
    (vault / "raw").mkdir(parents=True)
    (vault / "wiki").mkdir(parents=True)
    (vault / "wiki" / "_index.md").write_text("# Test")

    # Change to a random unrelated directory
    other_dir = tmp_path / "random-dir"
    other_dir.mkdir()
    monkeypatch.chdir(other_dir)

    monkeypatch.setenv("LEXWIKI_VAULT", str(vault))

    from lexwiki.config import load_config

    cfg = load_config()
    assert cfg.vault_dir == vault
    assert cfg.wiki_dir == vault / "wiki"
    assert (cfg.wiki_dir / "_index.md").exists()


def test_unset_mcpb_placeholder_is_ignored(monkeypatch):
    """Claude Desktop passes unset optional settings as literal ${user_config.*}."""
    from lexwiki.config import load_config

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setenv("LEXWIKI_MODEL", "${user_config.model}")
    monkeypatch.setenv("LEXWIKI_PROVIDER", "${user_config.llm_provider}")
    cfg = load_config()
    assert cfg.llm.provider == "openrouter"
    assert cfg.llm.model == "deepseek/deepseek-v4.1-flash"
