#!/usr/bin/env python3
"""Fail-closed same-day YouTube upload-attempt gate for GitHub Actions.

This is defense in depth, NOT cross-day SHA idempotency or publication approval.
Any prior workflow run in the Istanbul calendar day blocks another attempt,
including failed/unknown outcomes. No token or receipt content is logged.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ISTANBUL = ZoneInfo("Europe/Istanbul")
WORKFLOW = "youtube-upload.yml"


def assert_first_attempt_today(repo: str, run_id: int, token: str, *, now: datetime | None = None,
                               fetch=None) -> dict:
    if not repo or "/" not in repo or not token or run_id <= 0:
        raise ValueError("GitHub repository, run ID and actions:read token are required")
    now = now or datetime.now(ISTANBUL)
    local_date = now.astimezone(ISTANBUL).date()
    midnight = datetime.combine(local_date, time.min, tzinfo=ISTANBUL).astimezone(timezone.utc)
    tomorrow = (datetime.combine(local_date, time.min, tzinfo=ISTANBUL) +
                timedelta(days=1)).astimezone(timezone.utc)
    if fetch is None:
        fetch = _fetch
    seen_current = False
    for page in range(1, 21):
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        url = (f"https://api.github.com/repos/{repo}/actions/workflows/"
               f"{WORKFLOW}/runs?{query}")
        payload = fetch(url, token)
        runs = payload.get("workflow_runs")
        if not isinstance(runs, list):
            raise RuntimeError("GITHUB_RUNS_UNVERIFIED: invalid workflow response")
        for run in runs:
            try:
                created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                previous_id = int(run["id"])
            except (KeyError, ValueError, TypeError, AttributeError) as exc:
                raise RuntimeError("GITHUB_RUNS_UNVERIFIED: malformed workflow run") from exc
            if created.tzinfo is None:
                raise RuntimeError("GITHUB_RUNS_UNVERIFIED: timezone missing")
            if previous_id == run_id:
                seen_current = True
                continue
            if midnight <= created < tomorrow:
                raise RuntimeError(
                    "DAILY_UPLOAD_ATTEMPT_BLOCKED: another workflow run already exists "
                    f"for {local_date.isoformat()} Europe/Istanbul (run {previous_id}); "
                    "reconcile remote outcome before retry")
        # GitHub returns newest runs first. Continue until we have a complete
        # page containing an older day; never infer an empty page is safe
        # unless the current run is visible.
        if len(runs) < 100:
            if not seen_current:
                raise RuntimeError("GITHUB_RUNS_UNVERIFIED: current run not listed")
            return {"day": local_date.isoformat(), "current_run_id": run_id,
                    "same_day_other_attempts": 0, "gate": "PASS"}
    raise RuntimeError("GITHUB_RUNS_UNVERIFIED: pagination bound reached")


def _fetch(url: str, token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main() -> int:
    try:
        result = assert_first_attempt_today(
            os.environ.get("GITHUB_REPOSITORY", ""),
            int(os.environ.get("GITHUB_RUN_ID", "0")),
            os.environ.get("GITHUB_TOKEN", ""),
        )
    except Exception as exc:
        print(f"UPLOAD_ATTEMPT_GATE_BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
