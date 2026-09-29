from scripts.desk_health_normalize import normalize_health


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
