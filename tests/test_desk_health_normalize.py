import datetime as dt

from scripts.desk_health_normalize import (
    collect_active_ids,
    collect_message_source_statuses,
    normalize_health,
    reconcile_terminal_delivery,
)


def test_normalize_health_uses_active_source_ids_and_hourly_schedule():
    health = {
        "counts": {"pending": 9, "seen": 9, "answered": 9, "delayed": 9},
        "schedule": "*/15 * * * *",
        "retry": "old",
    }
    ledger = {
        "messages": {
            "MSG-live": {"status": "pending"},
            "MSG-old": {"status": "delayed"},
            "RPT-live": {"status": "answered"},
        }
    }

    out = normalize_health(health, ledger, {"MSG-live", "RPT-live"})

    assert out["counts"] == {"pending": 1, "seen": 0, "answered": 1, "delayed": 0}
    assert out["historical_counts"] == {"pending": 1, "seen": 0, "answered": 1, "delayed": 1}
    assert out["schedule"] == "0 * * * *"
    assert "hourly schedule" in out["retry"]
    assert out["normalized_by"] == "scripts/desk_health_normalize.py"


def test_terminal_source_clears_false_delayed_delivery():
    ledger = {
        "messages": {
            "MSG-done": {
                "status": "delayed",
                "message_status": "open",
                "needs_reply": True,
                "transitions_emitted": ["pending", "delayed"],
            },
            "MSG-open": {"status": "delayed", "message_status": "open", "needs_reply": True},
        }
    }
    changed = reconcile_terminal_delivery(
        ledger,
        {"MSG-done": "done", "MSG-open": "open"},
        dt.datetime(2026, 9, 29, 5, 0, tzinfo=dt.timezone(dt.timedelta(hours=3))),
    )

    assert changed == 1
    assert ledger["messages"]["MSG-done"]["status"] == "answered"
    assert ledger["messages"]["MSG-done"]["message_status"] == "done"
    assert ledger["messages"]["MSG-done"]["needs_reply"] is False
    assert "answered" in ledger["messages"]["MSG-done"]["transitions_emitted"]
    assert ledger["messages"]["MSG-open"]["status"] == "delayed"


def test_collect_message_source_statuses_reads_latest_message_status(tmp_path):
    (tmp_path / "shared-inbox.md").write_text(
        """
---
id: MSG-1
from: system
to: team
status: open
---
first

---
id: MSG-1
from: system
to: team
status: done
---
updated
""".lstrip(),
        encoding="utf-8",
    )
    assert collect_message_source_statuses(tmp_path)["MSG-1"] == "done"


def test_active_ids_ignore_archives_and_unwatched_message_files(tmp_path):
    (tmp_path / "shared-inbox.md").write_text("---\nid: MSG-live\nstatus: open\n---\nbody\n", encoding="utf-8")
    (tmp_path / "team-reports.md").write_text("## RPT-live\n- status: done\n", encoding="utf-8")
    (tmp_path / "team-reports-archive-20260927.md").write_text("## RPT-old\n- status: done\n", encoding="utf-8")
    (tmp_path / "user-action-required.md").write_text("---\nid: MSG-manual\nstatus: open\n---\nbody\n", encoding="utf-8")

    assert collect_active_ids(tmp_path) == {"MSG-live", "RPT-live"}
