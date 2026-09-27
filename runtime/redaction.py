from __future__ import annotations

import re
from typing import Any, Iterable


def redact_text(text: str, secret_values: Iterable[str]) -> str:
    out = str(text)
    for secret in secret_values:
        if secret:
            out = out.replace(str(secret), "[REDACTED]")
    out = re.sub(r"(?i)(authorization\s*:\s*)([^\r\n]+)", r"\1[REDACTED]", out)
    out = re.sub(r"(?i)\bBearer\s+[^\s,;]+", "Bearer [REDACTED]", out)
    out = re.sub(r"(?i)((?:set-)?cookie\s*:\s*)([^\r\n]+)", r"\1[REDACTED]", out)
    return out


def sanitize_object(value: Any, secret_values: Iterable[str]) -> Any:
    secrets = tuple(secret_values)
    if isinstance(value, str):
        return redact_text(value, secrets)
    if isinstance(value, dict):
        return {key: sanitize_object(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_object(item, secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_object(item, secrets) for item in value)
    return value
