from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .providers import ResearchProvider


@dataclass(frozen=True)
class ResearchResult:
    status: str
    provider: Optional[str] = None
    fallback_reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ResearchWorker:
    def __init__(self, providers: list[ResearchProvider]):
        self.providers = sorted(providers, key=lambda provider: provider.priority)

    def research(self, query: str, purpose: str) -> ResearchResult:
        available = [provider for provider in self.providers if provider.available]
        if not available:
            return ResearchResult(
                status="blocked",
                metadata=self._metadata(query, purpose, None),
            )

        selected = available[0]
        preferred = self.providers[0] if self.providers else None
        degraded = preferred is not None and selected.name != preferred.name
        return ResearchResult(
            status="degraded" if degraded else "ready",
            provider=selected.name,
            fallback_reason=(
                f"Preferred provider {preferred.name} is unavailable"
                if degraded and preferred is not None
                else None
            ),
            metadata=self._metadata(query, purpose, selected.name),
        )

    @staticmethod
    def _metadata(query: str, purpose: str, provider: Optional[str]) -> dict[str, Any]:
        return {
            "query": query,
            "purpose": purpose,
            "source_provider": provider,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
