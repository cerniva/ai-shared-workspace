import unittest
from datetime import datetime, timezone

from runtime.github_client import GitHubConflict
from runtime.status_store import StatusStore


class FakeClient:
    def __init__(self):
        self.data = {"version": 1, "items": [{"idempotency_key": "OTHER:1", "status": "succeeded"}]}
        self.sha = "s1"
        self.put_calls = 0

    def get_json(self, path):
        return self.data, self.sha

    def put_json(self, path, data, sha, message):
        self.put_calls += 1
        if self.put_calls == 1:
            raise GitHubConflict("conflict")
        self.data = data
        self.sha = "s2"
        return self.sha


class StatusStoreTests(unittest.TestCase):
    def task(self):
        return {"id": "A", "generation": 1, "connector": "synthetic", "operation": "echo", "action_class": "prepare"}

    def test_begin_finish_and_terminal_lookup(self):
        store = StatusStore({"version": 1, "items": []}, "sha0")
        now = datetime(2026, 9, 27, tzinfo=timezone.utc)
        started = store.begin(self.task(), now)
        self.assertEqual(started["status"], "running")
        done = store.finish("A:1", status="succeeded", summary="ok", error_code=None, retryable=False, now=now)
        self.assertEqual(done["status"], "succeeded")
        self.assertTrue(store.is_terminal("A:1"))

    def test_recent_running_entry_is_active_but_stale_one_is_not(self):
        data = {"version": 1, "items": [{
            "idempotency_key": "A:1", "status": "running", "started_at": "2026-09-27T00:00:00+00:00"
        }]}
        store = StatusStore(data, "sha0")
        self.assertTrue(store.is_active_running("A:1", datetime(2026, 9, 27, 0, 4, tzinfo=timezone.utc), lease_seconds=300))
        self.assertFalse(store.is_active_running("A:1", datetime(2026, 9, 27, 0, 6, tzinfo=timezone.utc), lease_seconds=300))

    def test_conflict_refetch_merges_without_overwriting_unrelated_rows(self):
        store = StatusStore({"version": 1, "items": []}, "stale")
        now = datetime(2026, 9, 27, tzinfo=timezone.utc)
        store.begin(self.task(), now)
        client = FakeClient()
        store.merge_and_write(client)
        keys = {item["idempotency_key"] for item in client.data["items"]}
        self.assertEqual(keys, {"OTHER:1", "A:1"})
        self.assertEqual(client.put_calls, 2)


if __name__ == "__main__":
    unittest.main()
