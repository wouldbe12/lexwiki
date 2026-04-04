"""Rough token counting for budget management."""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Estimate token count. ~4 chars per token is a reasonable average across models."""
    return len(text) // 4


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... truncated ...]"
