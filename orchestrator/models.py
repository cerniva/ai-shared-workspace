from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Job:
    kind: str
    action: str
    allow_browser_fallback: bool = False
    safety_gated: bool = False
    approved: bool = False


@dataclass(frozen=True)
class Provider:
    name: str
    mode: str
    available: bool = False


@dataclass(frozen=True)
class JobResult:
    status: str
    provider: Optional[str] = None
    fallback_reason: Optional[str] = None
