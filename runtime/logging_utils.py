from datetime import datetime, timezone


def build_log_record(*, task_id, connector, operation, status, duration_ms, error_code):
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "connector": connector,
        "operation": operation,
        "status": status,
        "duration_ms": duration_ms,
        "error_code": error_code,
    }
