from __future__ import annotations

import os
from collections.abc import Mapping

from scripts.worker_adapters import GeminiAdapter, GrokAdapter, MissingCredential, OpenAIAdapter, RetryableProviderError


class ConfigError(RuntimeError):
    pass


def make_adapter(provider: str, *, env: Mapping[str, str] | None = None):
    values = os.environ if env is None else env
    provider = provider.lower().strip()
    if provider == "openai":
        key = values.get("OPENAI_API_KEY")
        if not key or not key.strip():
            raise MissingCredential("openai API credential is missing")
        return OpenAIAdapter(
            api_key=key,
            model=values.get("OPENAI_MODEL", "gpt-5.6-sol"),
            reasoning_effort=values.get("OPENAI_REASONING_EFFORT", "medium"),
        )
    if provider == "grok":
        key = values.get("XAI_API_KEY")
        if not key or not key.strip():
            raise MissingCredential("grok API credential is missing")
        return GrokAdapter(api_key=key, model=values.get("XAI_MODEL", "grok-4.7"))
    if provider == "gemini":
        key = values.get("GEMINI_API_KEY")
        if not key or not key.strip():
            raise MissingCredential("gemini API credential is missing")
        return GeminiAdapter(api_key=key, model=values.get("GEMINI_MODEL", "gemini-3.6-flash"))
    raise ConfigError(f"unknown provider: {provider}")


class FailoverAdapter:
    """Try configured providers in order when a provider is temporarily unavailable."""
    provider = "failover"
    model = "automatic"

    def __init__(self, adapters):
        self.adapters = adapters

    def run(self, job):
        errors = []
        for adapter in self.adapters:
            try:
                return adapter.run(job)
            except (RetryableProviderError, MissingCredential) as exc:
                errors.append(f"{adapter.provider}: {exc}")
        raise RetryableProviderError("all configured providers unavailable: " + " | ".join(errors))


def make_failover_adapter(*, env: Mapping[str, str] | None = None):
    values = os.environ if env is None else env
    adapters = []
    if values.get("OPENAI_API_KEY", "").strip():
        adapters.append(make_adapter("openai", env=values))
    if values.get("XAI_API_KEY", "").strip():
        adapters.append(make_adapter("grok", env=values))
    if values.get("GEMINI_API_KEY", "").strip():
        adapters.append(make_adapter("gemini", env=values))
    if not adapters:
        raise MissingCredential("no AI provider credential is configured")
    return FailoverAdapter(adapters)
