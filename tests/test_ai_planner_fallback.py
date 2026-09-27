import pytest
import browser_worker.ai_planner as planner


def test_explicit_provider_fails_closed(monkeypatch):
    """An explicitly selected vendor must never forward the objective elsewhere."""
    calls = []

    def fail(_objective):
        calls.append("anthropic")
        raise RuntimeError("preferred failed")

    def alternate(_objective):
        calls.append("openai")
        return {"id": "ai-browser", "steps": []}

    monkeypatch.setattr(
        planner,
        "_providers",
        lambda: (("anthropic", fail), ("openai", alternate)),
    )

    with pytest.raises(SystemExit):
        planner.plan("open example.com", provider="anthropic")

    assert calls == ["anthropic"]


def test_auto_falls_back_to_next_provider(monkeypatch):
    """Auto mode may try the next configured provider after a failure."""
    calls = []

    def fail(_objective):
        calls.append("openai")
        raise RuntimeError("openai failed")

    def succeed(_objective):
        calls.append("grok")
        return {"id": "ai-browser", "steps": []}

    monkeypatch.setattr(
        planner,
        "_providers",
        lambda: (("openai", fail), ("grok", succeed)),
    )

    task = planner.plan("open example.com", provider="auto")

    assert task["planner_provider"] == "grok"
    assert calls == ["openai", "grok"]


def test_auto_stops_after_first_success(monkeypatch):
    """Auto mode stops immediately after the first successful provider."""
    calls = []

    def first(_objective):
        calls.append("openai")
        return {"id": "ai-browser", "steps": []}

    def unused(_objective):
        calls.append("unused")
        raise RuntimeError("should not run")

    monkeypatch.setattr(
        planner,
        "_providers",
        lambda: (("openai", first), ("grok", unused), ("gemini", unused), ("anthropic", unused)),
    )

    task = planner.plan("open example.com", provider="auto")

    assert task["planner_provider"] == "openai"
    assert calls == ["openai"]
