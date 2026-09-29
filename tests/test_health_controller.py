from scripts.health_controller import decide_action
from scripts.system_health import HealthEvidence


def ev(status):
    return HealthEvidence("worker", status, "2026-09-29T00:00:00+00:00")


def test_failed_allowlisted_target_requests_repair_then_retest():
    decision = decide_action(ev("failed"), target="scripts/worker_runner.py", repair="restart_worker")
    assert decision.action == "repair_then_retest"
    assert decision.requires_retest is True


def test_external_wait_and_optional_never_auto_repair():
    assert decide_action(ev("external_wait"), target="youtube", repair="restart_worker").action == "wait_external"
    assert decide_action(ev("disabled_optional"), target="grok", repair="restart_worker").action == "no_action"


def test_unknown_repair_fails_closed():
    assert decide_action(ev("failed"), target="scripts/worker.py", repair="delete_everything").action == "manual_review"


def test_payoutlens_rejected():
    decision = decide_action(ev("failed"), target="PayoutLens/app.py", repair="restart_worker")
    assert decision.action == "protected"
