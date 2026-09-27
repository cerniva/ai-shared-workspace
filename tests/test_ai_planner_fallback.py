import browser_worker.ai_planner as planner


def test_preferred_provider_falls_back(monkeypatch):
    def fail(_objective):
        raise RuntimeError("preferred failed")

    def succeed(_objective):
        return {"id": "ai-browser", "steps": []}

    monkeypatch.setattr(
        planner,
        "_providers",
        lambda: (("anthropic", fail), ("openai", succeed), ("grok", fail), ("gemini", fail)),
    )

    task = planner.plan("open example.com", provider="anthropic")

    assert task["planner_provider"] == "openai"


def test_auto_keeps_provider_order(monkeypatch):
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
