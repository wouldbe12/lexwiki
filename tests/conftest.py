"""Shared test fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary LexWiki project structure."""
    from lexwiki.config import init_project
    init_project(tmp_path)
    return tmp_path


@pytest.fixture
def sample_text():
    """A short legal document as plain text."""
    return """\
MASTER SERVICES AGREEMENT

This Master Services Agreement ("Agreement") is entered into as of January 1, 2026,
by and between ClientCo Ltd ("Client") and ServiceProvider Inc ("Provider").

1. SERVICES
Provider shall provide the services described in each Statement of Work.

2. TERM
This Agreement shall commence on the Effective Date and continue for three (3) years.

3. PAYMENT
Client shall pay Provider within thirty (30) days of receipt of each invoice.

4. LIMITATION OF LIABILITY
Neither party's total liability shall exceed GBP 5,000,000.

5. GOVERNING LAW
This Agreement shall be governed by the laws of England and Wales.
"""
