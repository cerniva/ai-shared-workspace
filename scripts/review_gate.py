from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from scripts.work_queue import WorkQueue

UTC = timezone.utc
VALID_VERDICTS = {"accept", "reject", "merge"}


def _append_lessons(
    path: Path,
    *,
    job_id: str,
    verdict: str,
    rationale: str,
    action: str,
    metric: str,
    lessons: Iterable[str],
    now: datetime,
) -> None:
    cleaned = [lesson.strip() for lesson in lessons if lesson and lesson.strip()]
    if not cleaned:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "",
        f"## {now.astimezone(UTC).isoformat()} — {job_id}",
        f"- verdict: {verdict}",
        f"- rationale: {rationale}",
        f"- action: {action}",
        f"- metric: {metric}",
        "- lessons:",
    ]
    lines.extend(f"  - {lesson}" for lesson in cleaned)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def review_job(
    queue: WorkQueue,
    job_id: str,
    *,
    verdict: str,
    rationale: str,
    action: str,
    metric: str,
    accepted_lessons: list[str] | None = None,
    lessons_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict:
    if verdict not in VALID_VERDICTS:
        raise ValueError(f"invalid verdict: {verdict}")
    now = now or datetime.now(UTC)
    review = {
        "verdict": verdict,
        "rationale": rationale,
        "accepted_lessons": list(accepted_lessons or []),
        "action": action,
        "metric": metric,
    }
    state = queue.mark_reviewed(job_id, review, now=now)
    if verdict not in {"accept", "merge"}:
        return state

    if lessons_path is not None:
        _append_lessons(
            Path(lessons_path),
            job_id=job_id,
            verdict=verdict,
            rationale=rationale,
            action=action,
            metric=metric,
            lessons=review["accepted_lessons"],
            now=now,
        )
    return queue.mark_applied(job_id, now=now)
