from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    github_token: str
    github_repo: str = "cerniva/ai-shared-workspace"
    poll_seconds: int = 60
    runtime_id: str = "replit-runtime-v1"

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        token = (env.get("GITHUB_TOKEN") or "").strip()
        repo = (env.get("GITHUB_REPO") or "cerniva/ai-shared-workspace").strip()
        runtime_id = (env.get("RUNTIME_ID") or "replit-runtime-v1").strip()
        try:
            poll = int(env.get("POLL_SECONDS") or "60")
            if poll <= 0:
                raise ValueError
        except (TypeError, ValueError):
            poll = 60
        return cls(token, repo, poll, runtime_id)

    @property
    def ready_for_github(self) -> bool:
        return bool(self.github_token and self.github_repo)

    def __repr__(self) -> str:
        return (
            "Settings("
            f"github_configured={bool(self.github_token)!r}, "
            f"github_repo={self.github_repo!r}, "
            f"poll_seconds={self.poll_seconds}, "
            f"runtime_id={self.runtime_id!r})"
        )
