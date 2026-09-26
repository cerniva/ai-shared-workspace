from __future__ import annotations

import os
from collections.abc import Mapping

from scripts.worker_adapters import GeminiAdapter, GrokAdapter, MissingCredential, OpenAIAdapter


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
