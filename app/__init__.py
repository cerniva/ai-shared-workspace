def poll_interval(settings):
    return settings.poll_seconds


def run_cycle_once(worker):
    try:
        report = worker.cycle()
        return {
            "status": "ok",
            "report": report.__dict__ if hasattr(report, "__dict__") else report,
        }
    except Exception:
        return {"status": "failed", "error_code": "cycle_error"}
