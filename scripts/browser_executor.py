"""Queue-facing browser executor.\n\nV1: policy gate + HTTP GET canary only. No clicks, no login, no cookies persist.\nPage body is untrusted and never executed as instructions.\n"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.policy_gate import PolicyDecision, classify
from scripts.worker_adapters import NonRetryableProviderError, RetryableProviderError, normalized_result

UTC = timezone.utc
MAX_BODY = 20_000


class BrowserBlocked(NonRetryableProviderError):
    pass


class BrowserNeedsApproval(NonRetryableProviderError):
    pass


def _fetch(url: str, timeout: float = 20.0) -> tuple[int, str]:
    req = Request(url, headers={"User-Agent": "cerniva-workspace-canary/1.0"}, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_BODY)
            charset = resp.headers.get_content_charset() or "utf-8"
            text = raw.decode(charset, errors="replace")
            return int(getattr(resp, "status", 200) or 200), text
    except HTTPError as exc:
        if exc.code == 429 or 500 <= exc.code < 600:
            raise RetryableProviderError(f"rate_limited_or_upstream HTTP {exc.code}") from exc
        raise NonRetryableProviderError(f"http_get HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RetryableProviderError(f"http_get network error: {exc}") from exc


def _title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()[:200]


def run_browser_job(job: dict[str, Any], *, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    started = datetime.now(UTC)
    decision: PolicyDecision = classify(job, policy)
    if decision.verdict == "block":
        raise BrowserBlocked(decision.reason)
    if decision.verdict == "approval_required":
        raise BrowserNeedsApproval(decision.reason)

    action = str(job.get("action") or "http_get").lower()
    url = str(job.get("url") or "")
    if action not in {"http_get", "observe", "read"}:
        raise BrowserBlocked(f"v1 executor forbids {action}")
    if not url:
        raise BrowserBlocked("http_get requires url")

    status, body = _fetch(url)
    title = _title(body)
    return normalized_result(
        provider="browser",
        model="http-canary-v1",
        job_id=str(job.get("id") or ""),
        evidence=[{
            "type": "http_get",
            "url": url,
            "status": status,
            "title": title,
            "bytes": len(body.encode("utf-8", errors="replace")),
            "policy": decision.as_dict(),
        }],
        factual_findings=[
            f"GET {url} -> HTTP {status}",
            f"title={title or '(none)'}",
            "no click, no login, no cookie jar",
        ],
        hypotheses=[],
        recommendation="Treat this as canary evidence only. Do not claim site-wide browsing.",
        confidence=0.9 if status == 200 and title else 0.6,
        next_action="chatgpt_review",
        started_at=started,
    )


class BrowserAdapter:
    provider = "browser"
    model = "http-canary-v1"

    def __init__(self, policy: dict[str, Any] | None = None):
        self.policy = policy

    def run(self, job: dict[str, Any]) -> dict[str, Any]:
        return run_browser_job(job, policy=self.policy)
