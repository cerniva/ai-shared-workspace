"""Classify external actions before any API or browser call."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "external_action_policy.json"

CRITICAL_ACTIONS = frozenset({
    "login",
    "oauth",
    "secret_entry",
    "payment",
    "financial_transaction",
    "account_security_change",
    "permission_change",
    "delete",
    "bulk_destructive_action",
    "irreversible_action",
    "checkout",
    "refund",
    "theme_publish",
    "price_write",
})

SAFE_OBSERVE = frozenset({"http_get", "observe", "read"})


class PolicyDecision:
    def __init__(self, verdict: str, reason: str, route: str = "none"):
        self.verdict = verdict
        self.reason = reason
        self.route = route

    def as_dict(self) -> dict[str, str]:
        return {"verdict": self.verdict, "reason": self.reason, "route": self.route}


def load_policy(path: str | Path | None = None) -> dict[str, Any]:
    target = Path(path) if path else DEFAULT_POLICY
    return json.loads(target.read_text(encoding="utf-8"))


def _host(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def classify(job: dict[str, Any], policy: dict[str, Any] | None = None) -> PolicyDecision:
    policy = policy or load_policy()
    action = str(job.get("action") or job.get("external_action") or "observe").strip().lower()
    url = str(job.get("url") or "")
    project = str(job.get("project") or "")
    approved = bool(job.get("approval") or job.get("human_approved"))
    mode = str(job.get("mode") or policy.get("default_mode") or "draft")

    if action in CRITICAL_ACTIONS and not approved:
        return PolicyDecision("approval_required", f"critical action requires human approval: {action}")

    if action not in SAFE_OBSERVE and mode == "observe":
        return PolicyDecision("block", f"observe mode forbids action {action}")

    routes = policy.get("routes") or {}
    if project == "shopify" or action.startswith("shopify_"):
        preferred = (routes.get("shopify") or {}).get("preferred_executor", "shopify_admin_graphql")
        if action in SAFE_OBSERVE or action.startswith("shopify_read"):
            return PolicyDecision("allow", "shopify read via API", route=preferred)
        if not approved:
            return PolicyDecision("approval_required", "shopify write requires approval", route=preferred)
        return PolicyDecision("allow", "shopify write approved", route=preferred)

    if url:
        allowed = {_host(f"https://{d}") if "." in d else d for d in (policy.get("allowed_domains") or [])}
        host = _host(url)
        if not allowed:
            return PolicyDecision("block", "browser domain allowlist is empty")
        if host not in allowed:
            return PolicyDecision("block", f"host not allowlisted: {host}")
        scheme = urlparse(url).scheme.lower()
        if scheme not in {"http", "https"}:
            return PolicyDecision("block", f"unsupported scheme: {scheme}")

    if action in SAFE_OBSERVE:
        return PolicyDecision("allow", "observe/http_get allowlisted", route="browser")

    if not approved:
        return PolicyDecision("approval_required", f"non-observe action needs approval: {action}", route="browser")
    return PolicyDecision("allow", "approved browser action", route="browser")
