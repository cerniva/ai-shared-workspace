#!/usr/bin/env python3
"""Shared multi-provider model fallback chain (single source: config/model_providers.json).

Order: GitHub Models -> Groq -> OpenRouter (:free) -> Cerebras -> Mistral ->
existing adapters (gemini, deepseek, claude, openai, grok via
scripts.provider_config.make_adapter) -> local small model (ollama, simple jobs only).

Usage (team-worker etc.)::

    from scripts.model_fallback import fallback_adapter, CannotDo
    adapter = fallback_adapter()          # None if nothing is configured
    result = adapter.run(job)             # raises CannotDo("YAPAMADIM: ...") if all fail

Errors are classified: no_key | quota (429) | billing (402/billing msg) |
auth (401/403) | error. Providers whose latest state/provider_health.json
status is auth/billing/error (fresh, < HEALTH_TTL) are tried last. Secrets are
never logged or included in messages.
"""
from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from scripts.worker_adapters import (
    UTC,
    MissingCredential,
    NonRetryableProviderError,
    SecretGuardedAdapter,
    Transport,
    WorkerError,
    _normalized_from_payload,
    _parse_json_text,
    _prompt,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "model_providers.json"
HEALTH_PATH = ROOT / "state" / "provider_health.json"
HEALTH_TTL = timedelta(hours=3)
STATUSES = ("ok", "no_key", "quota", "billing", "auth", "error")
_BILLING_RE = re.compile(r"billing|credit|payment|insufficient_quota|insufficient[_ ]funds|402", re.I)
_HTTP_RE = re.compile(r"HTTP (\d{3})")


class CannotDo(WorkerError):
    """All providers failed. Message always starts with 'YAPAMADIM:'."""


def load_config(path: Path = CONFIG_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))["providers"]


def classify(http_status: int | None, text: str = "") -> str:
    """Map an HTTP status / error text to a status. Text is never stored."""
    if http_status == 402 or (text and _BILLING_RE.search(text) and http_status != 401):
        return "billing"
    if http_status == 429:
        return "quota"
    if http_status in (401, 403):
        return "auth"
    if http_status is not None and 200 <= http_status < 300:
        return "ok"
    return "error"


def classify_exc(exc: Exception) -> str:
    if isinstance(exc, MissingCredential):
        return "no_key"
    status = getattr(exc, "http_status", None)
    if status is None:
        m = _HTTP_RE.search(str(exc))
        status = int(m.group(1)) if m else None
    return classify(status, str(exc) if status in (402, None) else "")


class OpenAICompatAdapter(SecretGuardedAdapter):
    """Generic OpenAI-compatible /chat/completions adapter (Groq, OpenRouter, ...)."""

    def __init__(self, provider: str, endpoint: str, api_key: str | None, model: str, *,
                 transport: Transport | None = None, timeout: float = 90.0, simple_only: bool = False):
        super().__init__(api_key, model, transport=transport, timeout=timeout)
        self.provider = provider
        self.endpoint = endpoint
        self.simple_only = simple_only

    def _request(self, job: dict[str, Any]) -> dict[str, Any]:
        started = datetime.now(UTC)
        tick = perf_counter()
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key != "local" else {}
        response = self.transport(
            self.endpoint, headers,
            {"model": self.model, "messages": [{"role": "user", "content": _prompt(job)}], "stream": False},
            self.timeout,
        )
        choices = response.get("choices") or []
        text = ((choices[0].get("message") or {}).get("content") or "") if choices else ""
        if not text:
            raise NonRetryableProviderError(f"{self.provider} response contained no message content")
        return _normalized_from_payload(
            _parse_json_text(text), provider=self.provider, model=str(response.get("model") or self.model),
            job_id=job["id"], started=started, duration_ms=int((perf_counter() - tick) * 1000),
            usage=response.get("usage") or {},
        )


def _model(spec: dict[str, Any], values: Mapping[str, str]) -> str:
    model = (values.get(spec.get("model_env", "")) or "").strip() or spec["model"]
    suffix = spec.get("require_suffix")
    if suffix and not model.endswith(suffix):
        model = spec["model"]  # never route OpenRouter to a paid model
    return model


def build_adapter(spec: dict[str, Any], values: Mapping[str, str], transport: Transport | None = None):
    """Return an adapter for ``spec`` or None if its credential/host is missing."""
    key = (values.get(spec["env"]) or "").strip()
    if not key:
        return None
    kind = spec["kind"]
    if kind == "openai_compat":
        return OpenAICompatAdapter(spec["name"], spec["endpoint"], key, _model(spec, values), transport=transport)
    if kind == "local":
        return OpenAICompatAdapter(spec["name"], key.rstrip("/") + spec["endpoint_path"], "local",
                                   _model(spec, values), transport=transport, timeout=180.0, simple_only=True)
    from scripts.provider_config import make_adapter
    adapter = make_adapter(spec["name"], env=values)
    if transport is not None and hasattr(adapter, "transport"):
        adapter.transport = transport
    return adapter


def _health_demoted(path: Path, now: datetime | None = None) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ts = datetime.fromisoformat(data["ts"])
    except Exception:
        return set()
    if (now or datetime.now(timezone.utc)) - ts > HEALTH_TTL:
        return set()
    return {p["name"] for p in data.get("providers", []) if p.get("status") in ("auth", "billing", "error")}


class ModelFallback:
    """Same ``run(job)`` interface as FailoverAdapter; tries every provider in order."""
    provider = "model_fallback"
    model = "automatic"

    def __init__(self, entries: list[tuple[str, Any]]):
        self.entries = entries  # (name, adapter|None)
        self.adapters = [a for _, a in entries if a is not None]
        self.attempts: list[dict[str, str]] = []

    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        self.attempts = []
        simple = bool(job.get("simple"))
        for name, adapter in self.entries:
            if adapter is None:
                self.attempts.append({"provider": name, "status": "no_key"})
                continue
            if getattr(adapter, "simple_only", False) and not simple:
                self.attempts.append({"provider": name, "status": "skipped_not_simple"})
                continue
            try:
                result = adapter.run(job)
            except WorkerError as exc:
                self.attempts.append({"provider": name, "status": classify_exc(exc)})
                continue
            self.attempts.append({"provider": name, "status": "ok"})
            return result
        tried = ", ".join(f"{a['provider']}={a['status']}" for a in self.attempts)
        raise CannotDo("YAPAMADIM: tum saglayicilar dustu; denenen: " + tried
                       + "; gereken: en az bir gecerli anahtar/kota (state/provider_health.json'a bakin)")


def fallback_adapter(*, env: Mapping[str, str] | None = None, config_path: Path = CONFIG_PATH,
                     health_path: Path = HEALTH_PATH, transport: Transport | None = None,
                     include: tuple[str, ...] | None = None) -> ModelFallback | None:
    """Build the shared chain. Returns None if no provider is configured at all."""
    values = os.environ if env is None else env
    specs = [s for s in load_config(config_path) if include is None or s["name"] in include]
    demoted = _health_demoted(health_path)
    specs = [s for s in specs if s["name"] not in demoted] + [s for s in specs if s["name"] in demoted]
    entries = [(s["name"], build_adapter(s, values, transport)) for s in specs]
    if not any(a is not None for _, a in entries):
        return None
    return ModelFallback(entries)
