"""Thin LLM client — direct HTTP calls to Anthropic, OpenAI, OpenRouter, and Ollama."""

from __future__ import annotations

import json
import os
import re

import httpx

from lexwiki.config import LLMConfig

# Default base URLs per provider
_BASE_URLS = {
    "anthropic": "https://api.anthropic.com",
    "openai": "https://api.openai.com",
    "openrouter": "https://openrouter.ai/api",
    "ollama": "http://localhost:11434",
}

_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


def _get_base_url(config: LLMConfig) -> str:
    if config.base_url:
        return config.base_url.rstrip("/")
    return _BASE_URLS.get(config.provider, _BASE_URLS["openai"])


def _get_api_key(config: LLMConfig) -> str:
    if config.provider == "ollama":
        return ""
    key = os.environ.get(config.api_key_env, "")
    if not key:
        raise ValueError(
            f"API key not found. Set the {config.api_key_env} environment variable."
        )
    return key


def complete(
    prompt: str,
    system: str = "",
    config: LLMConfig | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> str:
    """Send a completion request to the configured LLM provider.

    Supports Anthropic, OpenAI, OpenRouter, and Ollama.
    """
    cfg = config or LLMConfig()
    if not cfg.model:
        raise ValueError(
            f"No model configured for provider '{cfg.provider}'. Set LEXWIKI_MODEL."
        )
    base_url = _get_base_url(cfg)
    api_key = _get_api_key(cfg)
    mt = max_tokens or cfg.max_tokens
    temp = temperature if temperature is not None else cfg.temperature

    if cfg.provider == "anthropic":
        return _call_anthropic(base_url, api_key, cfg.model, prompt, system, mt)
    elif cfg.provider == "ollama":
        return _call_ollama(base_url, cfg.model, prompt, system, mt, temp)
    else:
        # openai and openrouter share the same API shape
        return _call_openai_compat(
            base_url, api_key, cfg.model, prompt, system, mt, temp,
            disable_reasoning=cfg.provider == "openrouter",
        )


def complete_structured(
    prompt: str,
    system: str = "",
    config: LLMConfig | None = None,
) -> dict | list:
    """Like complete() but extracts and parses JSON from the response."""
    raw = complete(prompt, system=system, config=config)
    return _extract_json(raw)


def _call_anthropic(
    base_url: str, api_key: str, model: str,
    prompt: str, system: str, max_tokens: int,
) -> str:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    # No temperature: current Claude models (Sonnet 5, Opus 4.7+) reject
    # sampling parameters with a 400.
    body: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    resp = httpx.post(
        f"{base_url}/v1/messages", headers=headers, json=body, timeout=_TIMEOUT
    )
    resp.raise_for_status()
    data = resp.json()
    # Models that think by default put thinking blocks before the text.
    return "".join(b["text"] for b in data["content"] if b["type"] == "text")


def _call_openai_compat(
    base_url: str, api_key: str, model: str,
    prompt: str, system: str, max_tokens: int, temperature: float,
    disable_reasoning: bool = False,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    url = f"{base_url}/v1/chat/completions"
    if disable_reasoning:
        # OpenRouter's unified reasoning switch. Compile and query don't
        # benefit from thinking, and on reasoning models it eats the output
        # budget. Models where reasoning is mandatory reject this with a 400;
        # retry those once at low effort so thinking can't take the whole budget.
        resp = httpx.post(
            url, headers=headers, json={**body, "reasoning": {"enabled": False}},
            timeout=_TIMEOUT,
        )
        if resp.status_code == 400 and "reasoning" in resp.text.lower():
            resp = httpx.post(
                url, headers=headers, json={**body, "reasoning": {"effort": "low"}},
                timeout=_TIMEOUT,
            )
    else:
        resp = httpx.post(url, headers=headers, json=body, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    choice = data["choices"][0]
    content = choice["message"].get("content")
    # Reasoning models (kimi, deepseek-r1) return content=null when max_tokens
    # is exhausted by chain-of-thought. Return empty string so retry logic kicks in.
    return content or ""


def _call_ollama(
    base_url: str, model: str,
    prompt: str, system: str, max_tokens: int, temperature: float,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        },
    }
    resp = httpx.post(f"{base_url}/api/chat", json=body, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]


def _extract_json(text: str) -> dict | list:
    """Extract JSON from LLM response, handling fenced code blocks."""
    # Try to find JSON in a fenced block first
    match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1).strip())
    # Try the whole text
    text = text.strip()
    # Find first { or [
    for i, ch in enumerate(text):
        if ch in "{[":
            return json.loads(text[i:])
    raise ValueError(f"No JSON found in LLM response: {text[:200]}")
