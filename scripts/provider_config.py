from __future__ import annotations

import os
from collections.abc import Mapping

from scripts.frontier_adapters import ClaudeAdapter, DeepSeekAdapter, PerplexityAdapter
from scripts.worker_adapters import (
    GeminiAdapter,
    GrokAdapter,
    MetaAdapter,
    MissingCredential,
    OpenAIAdapter,
    ProviderAuthError,
    RetryableProviderError,
)


class ConfigError(RuntimeError):
    pass


# Single source of truth for provider -> credential env name and team role.
# Only env *names* live here; values are read at runtime and never logged.
PROVIDER_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "grok": "XAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "meta": "META_MODEL_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

PROVIDER_ROLES: dict[str, str] = {
    "openai": "review_and_merge_decision",
    "grok": "builder_and_executor",
    "gemini": "second_opinion",
    "meta": "research_worker",
    "claude": "code_review_long_text",
    "perplexity": "research_with_citations",
    "deepseek": "cheap_analysis_and_code",
}

# Failover order: existing order first, new members appended.
FAILOVER_ORDER = ("gemini", "openai", "grok", "meta", "claude", "deepseek", "perplexity")


def providers_for_role(role: str) -> list[str]:
    return [name for name, value in PROVIDER_ROLES.items() if value == role]


def credential_status(*, env: Mapping[str, str] | None = None) -> dict[str, dict[str, str]]:
    """Names-only report: {provider: {env, status: configured|missing, role}}."""
    values = os.environ if env is None else env
    return {
        name: {
            "env": env_name,
            "status": "configured" if values.get(env_name, "").strip() else "missing",
            "role": PROVIDER_ROLES[name],
        }
        for name, env_name in PROVIDER_ENV.items()
    }


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
    if provider == "meta":
        key = values.get("META_MODEL_API_KEY")
        if not key or not key.strip():
            raise MissingCredential("meta API credential is missing")
        return MetaAdapter(api_key=key, model=values.get("META_MODEL", "muse-spark-1.3"))
    if provider == "claude":
        key = values.get("ANTHROPIC_API_KEY")
        if not key or not key.strip():
            raise MissingCredential("claude API credential is missing")
        return ClaudeAdapter(
            api_key=key,
            model=values.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
            workspace_id=values.get("ANTHROPIC_WORKSPACE_ID") or None,
        )
    if provider == "perplexity":
        key = values.get("PERPLEXITY_API_KEY")
        if not key or not key.strip():
            raise MissingCredential("perplexity API credential is missing")
        return PerplexityAdapter(api_key=key, model=values.get("PERPLEXITY_MODEL", "sonar"))
    if provider == "deepseek":
        key = values.get("DEEPSEEK_API_KEY")
        if not key or not key.strip():
            raise MissingCredential("deepseek API credential is missing")
        return DeepSeekAdapter(api_key=key, model=values.get("DEEPSEEK_MODEL", "deepseek-flash"))
    raise ConfigError(f"unknown provider: {provider}")


class FailoverAdapter:
    """Try configured providers in order when a provider is unavailable.

    A provider-scoped 401/403 (ProviderAuthError, e.g. Issue #101 xAI 403) must
    not block unrelated jobs: skip that provider and try the next one. If every
    provider failed only with auth/permission errors, or with auth errors plus
    missing credentials (no transient 429/5xx), raise ProviderAuthError
    (non-retryable) so the queue does not blind-retry a 403.
    """
    provider = "failover"
    model = "automatic"

    def __init__(self, adapters):
        self.adapters = adapters

    def run(self, job):
        errors = []
        transient = False
        last_auth = None
        for adapter in self.adapters:
            try:
                return adapter.run(job)
            except ProviderAuthError as exc:
                errors.append(f"{adapter.provider}: {exc}")
                last_auth = exc
            except MissingCredential as exc:
                # Config gap, not a transient outage: retrying unchanged cannot fix it.
                errors.append(f"{adapter.provider}: {exc}")
            except RetryableProviderError as exc:
                errors.append(f"{adapter.provider}: {exc}")
                transient = True
        message = "all configured providers unavailable: " + " | ".join(errors)
        # 403 + missing credential (no transient error) must not be blind-retried.
        if errors and last_auth is not None and not transient:
            raise ProviderAuthError(
                message,
                http_status=last_auth.http_status,
                endpoint_host=last_auth.endpoint_host,
                error_code=last_auth.error_code,
            )
        raise RetryableProviderError(message)


def make_failover_adapter(*, env: Mapping[str, str] | None = None):
    values = os.environ if env is None else env
    adapters = []
    for name in FAILOVER_ORDER:
        if values.get(PROVIDER_ENV[name], "").strip():
            adapters.append(make_adapter(name, env=values))
    if not adapters:
        raise MissingCredential("no AI provider credential is configured")
    return FailoverAdapter(adapters)
