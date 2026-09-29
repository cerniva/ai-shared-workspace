import json

from scripts.health_observability import append_local_event, combine_short_health


def test_local_jsonl_survives_external_sink_failure(tmp_path):
    path = tmp_path / "health.jsonl"
    def broken_sink(_event):
        raise RuntimeError("sink down")
    append_local_event(path, {"component": "worker", "status": "healthy"}, external_sink=broken_sink)
    saved = json.loads(path.read_text().strip())
    assert saved["status"] == "healthy"


def test_publish_external_wait_does_not_fail_production():
    result = combine_short_health(production="healthy", preflight="healthy", publish="external_wait")
    assert result["production"] == "healthy"
    assert result["publish"] == "external_wait"
    assert result["overall_production"] == "healthy"
