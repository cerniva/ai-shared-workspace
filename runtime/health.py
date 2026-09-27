def health_snapshot(worker):
    return {
        "service": "up",
        "github_configured": bool(worker.settings.ready_for_github),
        "github_last_ok": bool(worker.github_last_ok),
        "last_cycle_at": worker.last_cycle_at,
        "last_success_at": worker.last_success_at,
        "runtime_id": worker.settings.runtime_id,
    }
