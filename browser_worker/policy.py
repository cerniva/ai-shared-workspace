"""Fail-closed URL and action policy for the Actions browser worker."""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

SAFE_ACTIONS = {"goto", "wait", "wait_for", "extract", "screenshot"}
INTERACTIVE_ACTIONS = {"click", "fill", "type", "press"}
SENSITIVE_TERMS = re.compile(
    r"password|passwd|secret|token|api[_ -]?key|authorization|"
    r"credit.?card|card.?number|cvv|cvc|one.?time|otp|2fa|"
    r"current-password|new-password",
    re.IGNORECASE,
)
HIGH_IMPACT_TERMS = re.compile(
    r"publish|post\b|delete|remove|refund|checkout|purchase|buy\b|"
    r"pay\b|place order|submit order|send message|grant access|"
    r"change password|disable security|accept terms",
    re.IGNORECASE,
)
BLOCKED_HOSTS = {"localhost", "metadata.google.internal"}


class PolicyViolation(ValueError):
    """A browser action was blocked by policy."""


def normalize_allow_hosts(raw: str) -> set[str]:
    hosts: set[str] = set()
    for item in re.split(r"[,\s]+", raw.strip()):
        if not item:
            continue
        value = item.strip().lower().rstrip(".")
        if any(token in value for token in ("://", "/", "@", "?", "#")):
            raise PolicyViolation("allowed_hosts must contain bare hostnames only")
        try:
            host = value.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise PolicyViolation("invalid allowed hostname") from exc
        if (host in BLOCKED_HOSTS or host.endswith(".localhost")
                or host.endswith(".local") or host.endswith(".internal")):
            raise PolicyViolation("local/internal hosts cannot be allowlisted")
        hosts.add(host)
    if not hosts:
        raise PolicyViolation("allowed_hosts is required; default to example.com for a canary")
    return hosts


def host_is_allowed(host: str, allowed_hosts: set[str]) -> bool:
    candidate = host.rstrip(".").lower()
    try:
        candidate = candidate.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    return any(candidate == allowed or candidate.endswith("." + allowed)
               for allowed in allowed_hosts)


def safe_url(url: str, allowed_hosts: set[str]) -> str:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise PolicyViolation("only http/https URLs are allowed")
    if parsed.username or parsed.password:
        raise PolicyViolation("URLs containing embedded credentials are blocked")
    host = parsed.hostname
    if not host:
        raise PolicyViolation("URL host is required")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise PolicyViolation("private, loopback, and reserved IPs are blocked")
    if host.lower() in BLOCKED_HOSTS or host.lower().endswith((".localhost", ".local", ".internal")):
        raise PolicyViolation("local/internal hosts are blocked")
    if not host_is_allowed(host, allowed_hosts):
        raise PolicyViolation(f"host is outside allowlist: {host}")
    return url


def enforce_action(action: str, mode: str, target_label: str = "",
                   field_attributes: dict[str, str | None] | None = None) -> None:
    action = action.lower()
    mode = mode.lower()
    if action in SAFE_ACTIONS:
        return
    if action not in INTERACTIVE_ACTIONS:
        raise PolicyViolation(f"unsupported browser action: {action}")
    if mode != "interactive":
        raise PolicyViolation(f"approval_required: {action} needs interactive mode")
    label = target_label.strip()
    if action in {"click", "press"} and not label:
        raise PolicyViolation(f"approval_required: {action} requires an accessible target name")
    if HIGH_IMPACT_TERMS.search(label):
        raise PolicyViolation("approval_required: high-impact action target blocked")
    if action == "press" and label and re.search(r"^(enter|return)$", label, re.IGNORECASE):
        raise PolicyViolation("approval_required: Enter/Return can submit forms")
    attrs = field_attributes or {}
    metadata = " ".join(str(value or "") for value in attrs.values())
    if action in {"fill", "type"} and SENSITIVE_TERMS.search(label + " " + metadata):
        raise PolicyViolation("approval_required: sensitive fields are never filled by this worker")
