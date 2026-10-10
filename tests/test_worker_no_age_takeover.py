"""Regression: age alone cannot authorize a cross-worker claim."""
from datetime import datetime, timedelta, timezone

from scripts.run_next_worker import _fallback_reason, _eligible, SELF_NAME


def test_old_queued_job_is_not_automatically_stolen():
    now = datetime(2026, 10, 10, tzinfo=timezone.utc)
    job = {"worker": "grok", "status": "queued", "created_at": (now - timedelta(days=7)).isoformat()}
    assert not _fallback_reason(job, now, 60, set())
    assert not _eligible(job, now, 60, set())


def test_explicit_fallback_remains_allowed():
    now = datetime(2026, 10, 10, tzinfo=timezone.utc)
    job = {"worker": "grok", "status": "queued", "fallback_workers": [SELF_NAME]}
    assert _eligible(job, now, 60, set())


def test_down_provider_remains_allowed():
    now = datetime(2026, 10, 10, tzinfo=timezone.utc)
    job = {"worker": "grok", "status": "queued"}
    assert _eligible(job, now, 60, {"grok"})
