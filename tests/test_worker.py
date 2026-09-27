import unittest
from datetime import datetime, timezone

from runtime.settings import Settings
from runtime.worker import RuntimeWorker


class FakeClient:
    def __init__(self, dispatch, status=None):
        self.dispatch = dispatch
        self.status = status or {"version": 1, "items": []}
        self.sha_counter = 1
        self.get_calls = 0

    def get_json(self, path):
        self.get_calls += 1
        if path == "tasks/runtime-dispatch.json":
            return self.dispatch, "dispatch-sha"
        if path == "state/runtime-status.json":
            return self.status, f"s{self.sha_counter}"
        raise AssertionError(path)

    def put_json(self, path, data, sha, message):
        if path != "state/runtime-status.json":
            raise AssertionError(path)
        self.status = data
        self.sha_counter += 1
        return f"s{self.sha_counter}"


class RacingClient(FakeClient):
    def __init__(self, dispatch, now):
        super().__init__(dispatch)
        self.status_reads = 0
        self.now = now

    def get_json(self, path):
        if path == "state/runtime-status.json":
            self.status_reads += 1
            if self.status_reads == 1:
                return {"version": 1, "items": []}, "s1"
            self.status = {"version": 1, "items": [{
                "idempotency_key": "RUNTIME-SMOKE:1",
                "task_id": "RUNTIME-SMOKE",
                "generation": 1,
                "connector": "synthetic",
                "operation": "echo",
                "status": "running",
                "started_at": self.now.isoformat(),
                "claim_token": "other-worker",
            }]}
            return self.status, "s2"
        return super().get_json(path)

    def put_json(self, path, data, sha, message):
        raise AssertionError("losing worker must not overwrite another active claim")


class ExplodingConnector:
    def __init__(self):
        self.calls = 0

    def execute(self, operation, params):
        self.calls += 1
        raise RuntimeError("Authorization: Bearer SECRET cookie: sid=SECRET")


class CountingConnector:
    def __init__(self):
        self.calls = 0

    def execute(self, operation, params):
        self.calls += 1
        return {"summary": params.get("message", "")}


class WorkerTests(unittest.TestCase):
    def settings(self, token="SECRET"):
        return Settings.from_env({"GITHUB_TOKEN": token})

    def task(self):
        return {
            "id": "RUNTIME-SMOKE", "generation": 1, "task_type": "synthetic",
            "connector": "synthetic", "operation": "echo", "action_class": "prepare",
            "params": {"message": "hello"}, "created_at": "2026-09-27T00:00:00Z"
        }

    def test_success_emits_structured_safe_log(self):
        logs = []
        client = FakeClient({"version": 1, "items": [self.task()]})
        worker = RuntimeWorker(self.settings(), client=client, log_sink=logs.append)
        report = worker.cycle(datetime(2026, 9, 27, tzinfo=timezone.utc))
        self.assertEqual(report.succeeded, 1)
        self.assertEqual(len(logs), 1)
        row = logs[0]
        self.assertEqual(set(row), {"timestamp", "task_id", "connector", "operation", "status", "duration_ms", "error_code"})
        self.assertEqual(row["status"], "succeeded")
        self.assertNotIn("SECRET", str(row))

    def test_failure_emits_structured_safe_log(self):
        logs = []
        client = FakeClient({"version": 1, "items": [self.task()]})
        worker = RuntimeWorker(self.settings(), client=client, connectors={"synthetic": ExplodingConnector()}, log_sink=logs.append)
        report = worker.cycle(datetime(2026, 9, 27, tzinfo=timezone.utc))
        self.assertEqual(report.failed, 1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["status"], "failed")
        self.assertEqual(logs[0]["error_code"], "connector_error")
        self.assertNotIn("SECRET", str(logs[0]))

    def test_valid_task_executes_once_and_second_cycle_skips(self):
        client = FakeClient({"version": 1, "items": [self.task()]})
        connector = CountingConnector()
        worker = RuntimeWorker(self.settings(), client=client, connectors={"synthetic": connector})
        first = worker.cycle(datetime(2026, 9, 27, tzinfo=timezone.utc))
        second = worker.cycle(datetime(2026, 9, 27, 0, 1, tzinfo=timezone.utc))
        self.assertEqual(first.succeeded, 1)
        self.assertEqual(second.skipped, 1)
        self.assertEqual(connector.calls, 1)

    def test_racing_worker_loses_claim_without_executing_connector(self):
        now = datetime(2026, 9, 27, tzinfo=timezone.utc)
        client = RacingClient({"version": 1, "items": [self.task()]}, now)
        connector = CountingConnector()
        report = RuntimeWorker(self.settings(), client=client, connectors={"synthetic": connector}).cycle(now)
        self.assertEqual(report.skipped, 1)
        self.assertEqual(report.succeeded, 0)
        self.assertEqual(connector.calls, 0)

    def test_recent_running_task_is_not_reexecuted(self):
        status = {"version": 1, "items": [{
            "idempotency_key": "RUNTIME-SMOKE:1", "status": "running",
            "started_at": "2026-09-27T00:00:00+00:00"
        }]}
        client = FakeClient({"version": 1, "items": [self.task()]}, status=status)
        connector = CountingConnector()
        report = RuntimeWorker(self.settings(), client=client, connectors={"synthetic": connector}).cycle(
            datetime(2026, 9, 27, 0, 4, tzinfo=timezone.utc)
        )
        self.assertEqual(report.skipped, 1)
        self.assertEqual(connector.calls, 0)

    def test_future_contract_version_is_blocked_before_connector(self):
        client = FakeClient({"version": 2, "items": [self.task()]})
        connector = CountingConnector()
        report = RuntimeWorker(self.settings(), client=client, connectors={"synthetic": connector}).cycle()
        self.assertGreaterEqual(report.blocked, 1)
        self.assertEqual(connector.calls, 0)

    def test_malformed_task_is_blocked_before_connector(self):
        bad = self.task(); bad.pop("operation")
        client = FakeClient({"version": 1, "items": [bad]})
        connector = CountingConnector()
        report = RuntimeWorker(self.settings(), client=client, connectors={"synthetic": connector}).cycle()
        self.assertEqual(report.blocked, 1)
        self.assertEqual(connector.calls, 0)

    def test_connector_exception_is_sanitized(self):
        client = FakeClient({"version": 1, "items": [self.task()]})
        connector = ExplodingConnector()
        report = RuntimeWorker(self.settings(), client=client, connectors={"synthetic": connector}).cycle()
        self.assertEqual(report.failed, 1)
        text = str(client.status)
        self.assertNotIn("SECRET", text)
        self.assertNotIn("sid=", text)

    def test_missing_github_token_does_no_io(self):
        client = FakeClient({"version": 1, "items": [self.task()]})
        report = RuntimeWorker(self.settings(token=""), client=client).cycle()
        self.assertTrue(report.unready)
        self.assertEqual(client.get_calls, 0)


if __name__ == "__main__":
    unittest.main()
