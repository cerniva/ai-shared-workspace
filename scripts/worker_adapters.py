from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
from time import perf_counter
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

UTC = timezone.utc
Transport = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]


class WorkerError(RuntimeError):
    pass


class MissingCredential(WorkerError):
    pass


class ProviderNotConfigured(WorkerError):
    pass


class RetryableProviderError(WorkerError):
    pass


class NonRetryableProviderError(WorkerError):
    pass


def normalized_result(
    *,
    provider: str,
    model: str,
    job_id: str,
    evidence: list[dict[str, Any]] | None = None,
    factual_findings: list[str] | None = None,
    hypotheses: list[str] | None = None,
    recommendation: str = "",
    confidence: float = 0.0,
    next_action: str = "",
    started_at: datetime | None = None,
    duration_ms: int = 0,
    usage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started_at = started_at or datetime.now(UTC)
    return {
        "provider": provider,
        "model": model,
        "job_id": job_id,
        "evidence": evidence or [],
        "factual_findings": factual_findings or [],
        "hypotheses": hypotheses or [],
        "recommendation": recommendation,
        "confidence": float(confidence),
        "next_action": next_action,
        "timing": {
            "started_at": started_at.astimezone(UTC).isoformat(),
            "duration_ms": int(duration_ms),
        },
        "usage": usage or {},
    }


def _default_transport(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 429 or 500 <= exc.code < 600:
            raise RetryableProviderError(f"provider HTTP {exc.code}") from exc
        raise NonRetryableProviderError(f"provider HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RetryableProviderError("provider network error") from exc


def _prompt(job: dict[str, Any]) -> str:
    evidence_requirements = job.get("evidence_requirements") or []
    return (
        "You are an evidence-producing worker in a shared AI workspace. "
        "Return ONLY one JSON object with keys: evidence (array of objects), "
        "factual_findings (array of strings), hypotheses (array of strings), "
        "recommendation (string), confidence (number 0..1), next_action (string). "
        "Do not claim actions you did not perform.\n"
        f"Project: {job.get('project', 'workspace')}\n"
        f"Objective: {job.get('objective', '')}\n"
        f"Evidence requirements: {json.dumps(evidence_requirements, ensure_ascii=False)}"
    )


def _parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise NonRetryableProviderError("provider returned non-JSON worker result") from exc
    if not isinstance(value, dict):
        raise NonRetryableProviderError("provider returned invalid worker result")
    return value


def _normalized_from_payload(
    payload: dict[str, Any], *, provider: str, model: str, job_id: str, started: datetime, duration_ms: int, usage: dict[str, Any]
) -> dict[str, Any]:
    confidence = payload.get("confidence", 0.0)
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.0
    return normalized_result(
        provider=provider,
        model=model,
        job_id=job_id,
        evidence=payload.get("evidence") if isinstance(payload.get("evidence"), list) else [],
        factual_findings=payload.get("factual_findings") if isinstance(payload.get("factual_findings"), list) else [],
        hypotheses=payload.get("hypotheses") if isinstance(payload.get("hypotheses"), list) else [],
        recommendation=str(payload.get("recommendation", "")),
        confidence=confidence,
        next_action=str(payload.get("next_action", "")),
        started_at=started,
        duration_ms=duration_ms,
        usage=usage,
    )


class WorkerAdapter(ABC):
    provider: str
    model: str

    @abstractmethod
    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class MockAdapter(WorkerAdapter):
    def __init__(self, provider: str = "mock", model: str = "mock-v1"):
        self.provider = provider
        self.model = model

    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        started = datetime.now(UTC)
        tick = perf_counter()
        return normalized_result(
            provider=self.provider,
            model=self.model,
            job_id=job["id"],
            evidence=[{"type": "mock", "value": "deterministic"}],
            factual_findings=[f"Mock result for {job.get('objective', '')}"],
            hypotheses=[],
            recommendation="Review mock evidence before applying.",
            confidence=1.0,
            next_action="chatgpt_review",
            started_at=started,
            duration_ms=int((perf_counter() - tick) * 1000),
            usage={"input_tokens": 0, "output_tokens": 0, "cost": 0},
        )


class SecretGuardedAdapter(WorkerAdapter):
    provider = "provider"

    def __init__(self, api_key: str | None, model: str, *, transport: Transport | None = None, timeout: float = 45.0):
        self.api_key = api_key
        self.model = model
        self.transport = transport or _default_transport
        self.timeout = timeout
        self.request_count = 0

    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key or not self.api_key.strip():
            raise MissingCredential(f"{self.provider} API credential is missing")
        self.request_count += 1
        return self._request(job)

    @abstractmethod
    def _request(self, job: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class GrokAdapter(SecretGuardedAdapter):
    provider = "grok"

    def _request(self, job: dict[str, Any]) -> dict[str, Any]:
        started = datetime.now(UTC)
        tick = perf_counter()
        response = self.transport(
            "https://api.x.ai/v1/responses",
            {"Authorization": f"Bearer {self.api_key}"},
            {"model": self.model, "input": _prompt(job), "store": False},
            self.timeout,
        )
        text = ""
        for output in response.get("output", []):
            if output.get("type") != "message":
                continue
            for part in output.get("content", []):
                if part.get("type") == "output_text":
                    text += str(part.get("text", ""))
        if not text:
            raise NonRetryableProviderError("grok response contained no output_text")
        parsed = _parse_json_text(text)
        return _normalized_from_payload(
            parsed,
            provider=self.provider,
            model=str(response.get("model") or self.model),
            job_id=job["id"],
            started=started,
            duration_ms=int((perf_counter() - tick) * 1000),
            usage=response.get("usage") if isinstance(response.get("usage"), dict) else {},
        )


class GeminiAdapter(SecretGuardedAdapter):
    provider = "gemini"

    def _request(self, job: dict[str, Any]) -> dict[str, Any]:
        started = datetime.now(UTC)
        tick = perf_counter()
        response = self.transport(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            {"x-goog-api-key": str(self.api_key)},
            {"contents": [{"parts": [{"text": _prompt(job)}]}]},
            self.timeout,
        )
        text = ""
        candidates = response.get("candidates") or []
        if candidates:
            content = candidates[0].get("content") or {}
            for part in content.get("parts", []):
                if "text" in part:
                    text += str(part.get("text", ""))
        if not text:
            raise NonRetryableProviderError("gemini response contained no text")
        parsed = _parse_json_text(text)
        usage_meta = response.get("usageMetadata") if isinstance(response.get("usageMetadata"), dict) else {}
        usage = {
            "input_tokens": usage_meta.get("promptTokenCount"),
            "output_tokens": usage_meta.get("candidatesTokenCount"),
            "total_tokens": usage_meta.get("totalTokenCount"),
        }
        return _normalized_from_payload(
            parsed,
            provider=self.provider,
            model=self.model,
            job_id=job["id"],
            started=started,
            duration_ms=int((perf_counter() - tick) * 1000),
            usage=usage,
        )
