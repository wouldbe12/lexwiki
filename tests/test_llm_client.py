"""Request shape of the OpenAI-compatible client (HTTP stubbed)."""

import httpx

from lexwiki.config import LLMConfig
from lexwiki.llm import client


def _stub_post(monkeypatch, responses):
    sent = []

    def fake_post(url, headers=None, json=None, timeout=None):
        sent.append(json)
        status, payload = responses[len(sent) - 1]
        return httpx.Response(status, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(client.httpx, "post", fake_post)
    return sent


def _ok(text):
    return 200, {"choices": [{"message": {"content": text}}]}


def _complete(monkeypatch, provider):
    monkeypatch.setenv("LEXWIKI_TEST_KEY", "k")
    cfg = LLMConfig(provider=provider, model="m", api_key_env="LEXWIKI_TEST_KEY")
    return client.complete("hi", config=cfg)


def test_openrouter_disables_reasoning(monkeypatch):
    sent = _stub_post(monkeypatch, [_ok("done")])
    assert _complete(monkeypatch, "openrouter") == "done"
    assert sent[0]["reasoning"] == {"enabled": False}


def test_openrouter_mandatory_reasoning_falls_back_to_low(monkeypatch):
    refusal = (400, {"error": {"message": "Reasoning is mandatory for this endpoint"}})
    sent = _stub_post(monkeypatch, [refusal, _ok("done")])
    assert _complete(monkeypatch, "openrouter") == "done"
    assert sent[1]["reasoning"] == {"effort": "low"}


def test_openai_gets_no_reasoning_field(monkeypatch):
    sent = _stub_post(monkeypatch, [_ok("done")])
    _complete(monkeypatch, "openai")
    assert "reasoning" not in sent[0]
