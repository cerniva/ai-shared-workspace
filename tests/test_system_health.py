from datetime import datetime, timedelta, timezone

from scripts.system_health import HealthEvidence, effective_status, is_protected_target


def test_fresh_healthy_stays_healthy():
    now = datetime.now(timezone.utc)
    evidence = HealthEvidence("worker", "healthy", now.isoformat(), ttl_seconds=300)
    assert effective_status(evidence, now=now)[0] == "healthy"


def test_stale_healthy_becomes_degraded_stale_green():
    now = datetime.now(timezone.utc)
    evidence = HealthEvidence("worker", "healthy", (now - timedelta(seconds=301)).isoformat(), ttl_seconds=300)
    assert effective_status(evidence, now=now) == ("degraded", "stale_green")


def test_naive_now_is_interpreted_as_utc():
    checked = datetime(2026, 9, 29, 8, 0, tzinfo=timezone.utc)
    evidence = HealthEvidence("worker", "healthy", checked.isoformat(), ttl_seconds=300)
    assert effective_status(evidence, now=datetime(2026, 9, 29, 8, 4)) == ("healthy", "fresh_evidence")


def test_invalid_ttl_fails_closed():
    now = datetime.now(timezone.utc)
    evidence = HealthEvidence("worker", "healthy", now.isoformat(), ttl_seconds="bad")
    assert effective_status(evidence, now=now) == ("failed", "invalid_ttl")


def test_non_finite_ttl_fails_closed():
    now = datetime.now(timezone.utc)
    evidence = HealthEvidence("worker", "healthy", now.isoformat(), ttl_seconds=float("nan"))
    assert effective_status(evidence, now=now) == ("failed", "invalid_ttl")


def test_future_timestamp_fails_closed():
    now = datetime.now(timezone.utc)
    evidence = HealthEvidence("worker", "healthy", (now + timedelta(seconds=1)).isoformat(), ttl_seconds=300)
    assert effective_status(evidence, now=now) == ("failed", "future_evidence_timestamp")


def test_unknown_status_fails_closed():
    now = datetime.now(timezone.utc)
    evidence = HealthEvidence("worker", "mystery", now.isoformat(), ttl_seconds=300)
    assert effective_status(evidence, now=now)[0] == "failed"


def test_payoutlens_is_always_protected_case_insensitive():
    assert is_protected_target("PayoutLens/core.py")
    assert is_protected_target("tasks/pAyOuTlEnS-fix.md")
    assert not is_protected_target("scripts/worker.py")
