import unittest
from datetime import datetime, timedelta, timezone

from scripts import improvement_bot as ib

NOW = datetime(2026, 11, 25, 0, 0, tzinfo=timezone.utc)


def _report(prs):
    sug = {"key": "slow-auto-merge-gate", "kind": "speedup", "target": "x", "text": "speed up",
           "enriched_by": "rule"}
    return {"generated_at": NOW.isoformat(), "ranked_speedups": [sug], "bot_prs": prs}


def _item(status, days_ago):
    return {"id": "HO-IMP-20261107-slow-auto-merge-gate", "status": status,
            "created_at": (NOW - timedelta(days=days_ago)).isoformat()}


class OpenDedup(unittest.TestCase):
    def test_open_pr_older_than_window_blocks_reopen(self):
        prs = [{"number": 397, "branch": "bot/HO-IMP-20261107-slow-auto-merge-gate-42369802470"}]
        r = ib.plan_handoff(_report(prs), {"items": [_item("done", 18)]}, dry_run=True)
        self.assertEqual(r["status"], "no_new_suggestion")

    def test_open_handoff_older_than_window_blocks_reopen(self):
        r = ib.plan_handoff(_report([]), {"items": [_item("open", 18)]}, dry_run=True)
        self.assertEqual(r["status"], "no_new_suggestion")

    def test_closed_old_and_no_pr_allows_reopen(self):
        r = ib.plan_handoff(_report([]), {"items": [_item("done", 18)]}, dry_run=True)
        self.assertEqual(r["status"], "dry_run")

    def test_branch_key_parsing(self):
        keys = ib.open_keys({"items": []}, [{"branch": "bot/HO-IMP-20261124-slow-tinyfish-youtube-analytics-45432048265"},
                                             {"branch": "bot/CI-1-2"}])
        self.assertEqual(keys, {"slow-tinyfish-youtube-analytics"})


if __name__ == "__main__":
    unittest.main()
