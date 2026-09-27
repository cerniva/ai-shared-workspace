from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ShortsResult:
    status: str
    provider: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ShortsWorker:
    def __init__(self, youtube_api_available: bool = False):
        self.youtube_api_available = youtube_api_available

    def draft(self, topic: str, research_provider: str) -> ShortsResult:
        return ShortsResult(
            status="ready",
            metadata={"topic": topic, "research_provider": research_provider},
        )

    def analytics(self, video_id: str) -> ShortsResult:
        if not self.youtube_api_available:
            return ShortsResult(status="blocked", metadata={"video_id": video_id})
        return ShortsResult(
            status="ready",
            provider="youtube_api",
            metadata={"video_id": video_id},
        )

    def publish(self, video_path: str, approved: bool = False) -> ShortsResult:
        if not approved:
            return ShortsResult(
                status="approval_required",
                metadata={"video_path": video_path},
            )
        if not self.youtube_api_available:
            return ShortsResult(
                status="blocked",
                metadata={"video_path": video_path},
            )
        return ShortsResult(
            status="ready",
            provider="youtube_api",
            metadata={"video_path": video_path},
        )
