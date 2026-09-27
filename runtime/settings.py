from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


APPROVED_GITHUB_REPO = "cerniva/ai-shared-workspace"
APPROVED_GITHUB_BRANCH = "private-replit-runtime-v1"


@dataclass(frozen=True)
class Settings:
    github_token: str
    github_repo: str = APPROVED_GITHUB_REPO
    github_branch: str = APPROVED_GITHUB_BRANCH
    poll_seconds: int = 60
    runtime_id: str = "replit-runtime-v1"

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        token = (env.get("GITHUB_TOKEN") or "").strip()
        repo = (env.get("GITHUB_REPO") or APPROVED_GITHUB_REPO).strip()
        branch = (env.get("GITHUB_BRANCH") or APPROVED_GITHUB_BRANCH).strip() or APPROVED_GITHUB_BRANCH
        runtime_id = (env.get("RUNTIME_ID") or "replit-runtime-v1").strip()
        try:
            poll = int(env.get("POLL_SECONDS") or "60")
            if poll <= 0:
                raise ValueError
        except (TypeError, ValueError):
            poll = 60
        return cls(token, repo, branch, poll, runtime_id)

    @property
    def ready_for_github(self) -> bool:
        return bool(
            self.github_token
            and self.github_repo == APPROVED_GITHUB_REPO
            and self.github_branch == APPROVED_GITHUB_BRANCH
        )

    def __repr__(self) -> str:
        return (
            "Settings("
            f"github_configured={bool(self.github_token)!r}, "
            f"github_repo={self.github_repo!r}, "
            f"github_branch={self.github_branch!r}, "
            f"poll_seconds={self.poll_seconds}, "
            f"runtime_id={self.runtime_id!r})"
        )
