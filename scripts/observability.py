from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

UTC = timezone.utc

_SENSITIVE_KEY = re.compile(r"(?i)(secret|token|password|authorization|api[_-]?key|dsn)")
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xai-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._-]{20,}"),
)
_sentry_initialized_dsn: str | None = None


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)(Bearer"):
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _sanitize(value: Any, *, key: str | None = None) -> Any:
    if key is not None and _SENSITIVE_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, Mapping):
        return {str(k): _sanitize(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _redact_text(str(value))


def _write_local(event: dict[str, Any], env: Mapping[str, str]) -> None:
    raw_path = env.get("OBSERVABILITY_LOG_PATH")
    if not raw_path:
        return
    path = Path(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _emit_sentry(event: dict[str, Any], env: Mapping[str, str], exception: BaseException | None) -> None:
    global _sentry_initialized_dsn

    dsn = env.get("SENTRY_DSN")
    if not dsn:
        return

    import sentry_sdk  # type: ignore

    if _sentry_initialized_dsn != dsn:
        sentry_sdk.init(dsn=dsn)
        _sentry_initialized_dsn = dsn

    if exception is not None:
        sentry_sdk.capture_exception(exception)
    else:
        level = "error" if event["level"] == "ERROR" else "info"
        sentry_sdk.capture_message(
            f"{event['event']} {json.dumps(event, ensure_ascii=False, sort_keys=True)}",
            level=level,
        )


def _emit_langfuse(event: dict[str, Any], env: Mapping[str, str]) -> None:
    if not env.get("LANGFUSE_PUBLIC_KEY") or not env.get("LANGFUSE_SECRET_KEY"):
        return

    from langfuse import get_client  # type: ignore

    client = get_client()
    with client.start_as_current_observation(
        name=event["event"],
        as_type="span",
        metadata=event,
        level=event["level"],
        status_message=event.get("error"),
    ):
        pass
    client.flush()


def emit_event(
    event_name: str,
    payload: Mapping[str, Any] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    exception: BaseException | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Emit one sanitized lifecycle event without ever breaking the caller.

    Local JSONL is enabled with OBSERVABILITY_LOG_PATH. Sentry and Langfuse
    are optional sinks activated only when their credentials and SDKs exist.
    """

    values = os.environ if env is None else env
    sanitized = _sanitize(dict(payload or {}))
    level = "ERROR" if any(marker in event_name for marker in ("failed", "dead_letter", "blocked", "error")) else "DEFAULT"
    event = {
        "event": event_name,
        "timestamp": (timestamp or datetime.now(UTC)).astimezone(UTC).isoformat(),
        "level": level,
        **sanitized,
    }

    for sink in (
        lambda: _write_local(event, values),
        lambda: _emit_sentry(event, values, exception),
        lambda: _emit_langfuse(event, values),
    ):
        try:
            sink()
        except Exception:
            # Observability must remain fail-open. Sink health is inspected
            # independently; provider work must never fail because telemetry did.
            continue

    return event
