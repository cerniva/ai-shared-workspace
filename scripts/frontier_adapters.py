"""Adapters for Claude, Perplexity and DeepSeek (multi-AI roster, 2026-10-10).

Same contract as scripts/worker_adapters.py: SecretGuardedAdapter raises
MissingCredential on an empty key; HTTP 401/403 -> ProviderAuthError,
429/5xx -> RetryableProviderError (via the shared default transport).
Endpoints confirmed against official docs on 2026-10-10.
"""
from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any

from scripts.worker_adapters import (
    UTC,
    NonRetryableProviderError,
    SecretGuardedAdapter,
    Transport,
    _normalized_from_payload,
    _parse_json_text,
    _prompt,
)


def _anthropic_text(response: dict[str, Any]) -> str:
    text = ""
    for block in response.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text":
            text += str(block.get("text", ""))
    return text


def _chat_completion_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "")


def _usage(response: dict[str, Any]) -> dict[str, Any]:
    return response.get("usage") if isinstance(response.get("usage"), dict) else {}


class ClaudeAdapter(SecretGuardedAdapter):
    """Anthropic Messages API (POST https://api.anthropic.com/v1/messages).

    Role: code review and long-text analysis. Auth header x-api-key plus the
    required anthropic-version header; key from ANTHROPIC_API_KEY.
    """
    provider = "claude"
    endpoint = "https://api.anthropic.com/v1/messages"
    api_version = "2023-06-01"

    def __init__(self, api_key: str | None, model: str = "claude-sonnet-5-5", *, max_tokens: int = 4096,
                 workspace_id: str | None = None, transport: Transport | None = None, timeout: float = 90.0):
        super().__init__(api_key, model, transport=transport, timeout=timeout)
        self.max_tokens = max_tokens
        self.workspace_id = workspace_id

    def _request(self, job: dict[str, Any]) -> dict[str, Any]:
        started = datetime.now(UTC)
        tick = perf_counter()
        headers = {"x-api-key": str(self.api_key), "anthropic-version": self.api_version}
        if self.workspace_id and self.workspace_id.strip():
            headers["anthropic-workspace-id"] = self.workspace_id.strip()
        response = self.transport(
            self.endpoint,
            headers,
            {"model": self.model, "max_tokens": self.max_tokens,
             "messages": [{"role": "user", "content": _prompt(job)}]},
            self.timeout,
        )
        text = _anthropic_text(response)
        if not text:
            raise NonRetryableProviderError("claude response contained no text block")
        return _normalized_from_payload(
            _parse_json_text(text), provider=self.provider, model=str(response.get("model") or self.model),
            job_id=job["id"], started=started, duration_ms=int((perf_counter() - tick) * 1000),
            usage=_usage(response),
        )


def perplexity_citations(response: dict[str, Any]) -> list[dict[str, str]]:
    """Merge search_results (title/url/date) and bare citations URLs; order kept, deduped."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in response.get("search_results") or []:
        if isinstance(item, dict) and isinstance(item.get("url"), str) and item["url"] not in seen:
            entry = {"url": item["url"]}
            for key in ("title", "date"):
                if isinstance(item.get(key), str):
                    entry[key] = item[key]
            out.append(entry)
            seen.add(item["url"])
    for url in response.get("citations") or []:
        if isinstance(url, str) and url not in seen:
            out.append({"url": url})
            seen.add(url)
    return out


class PerplexityAdapter(SecretGuardedAdapter):
    """Perplexity Sonar chat completions (POST https://api.perplexity.ai/v1/sonar).

    Role: web research with citations. citations / search_results are kept in
    result["citations"] and appended to evidence as citation items so every
    claim stays verifiable. Key from PERPLEXITY_API_KEY.
    """
    provider = "perplexity"
    endpoint = "https://api.perplexity.ai/v1/sonar"

    def __init__(self, api_key: str | None, model: str = "sonar", *, transport: Transport | None = None,
                 timeout: float = 90.0):
        super().__init__(api_key, model, transport=transport, timeout=timeout)

    def _request(self, job: dict[str, Any]) -> dict[str, Any]:
        started = datetime.now(UTC)
        tick = perf_counter()
        response = self.transport(
            self.endpoint,
            {"Authorization": f"Bearer {self.api_key}"},
            {"model": self.model, "messages": [{"role": "user", "content": _prompt(job)}]},
            self.timeout,
        )
        text = _chat_completion_text(response)
        if not text:
            raise NonRetryableProviderError("perplexity response contained no message content")
        result = _normalized_from_payload(
            _parse_json_text(text), provider=self.provider, model=str(response.get("model") or self.model),
            job_id=job["id"], started=started, duration_ms=int((perf_counter() - tick) * 1000),
            usage=_usage(response),
        )
        citations = perplexity_citations(response)
        result["citations"] = citations
        seen = {str(e.get("url")) for e in result["evidence"] if isinstance(e, dict) and e.get("url")}
        for item in citations:
            if item["url"] not in seen:
                result["evidence"].append({"type": "citation", **item})
                seen.add(item["url"])
        return result


class DeepSeekAdapter(SecretGuardedAdapter):
    """DeepSeek OpenAI-compatible chat completions (POST https://api.deepseek.com/chat/completions).

    Role: low-cost analysis and code. Key from DEEPSEEK_API_KEY.
    """
    provider = "deepseek"
    endpoint = "https://api.deepseek.com/chat/completions"

    def __init__(self, api_key: str | None, model: str = "deepseek-flash", *, transport: Transport | None = None,
                 timeout: float = 90.0):
        super().__init__(api_key, model, transport=transport, timeout=timeout)

    def _request(self, job: dict[str, Any]) -> dict[str, Any]:
        started = datetime.now(UTC)
        tick = perf_counter()
        response = self.transport(
            self.endpoint,
            {"Authorization": f"Bearer {self.api_key}"},
            {"model": self.model, "messages": [{"role": "user", "content": _prompt(job)}], "stream": False},
            self.timeout,
        )
        text = _chat_completion_text(response)
        if not text:
            raise NonRetryableProviderError("deepseek response contained no message content")
        return _normalized_from_payload(
            _parse_json_text(text), provider=self.provider, model=str(response.get("model") or self.model),
            job_id=job["id"], started=started, duration_ms=int((perf_counter() - tick) * 1000),
            usage=_usage(response),
        )
