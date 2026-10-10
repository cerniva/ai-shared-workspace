import copy
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from scripts import improvement_bot as ib
from scripts import handoff
from scripts.model_fallback import CannotDo

NOW = datetime(2026, 10, 12, 6, 23, tzinfo=timezone.utc)


def run(name, path, minutes, conclusion="success", ago_h=24):
    start = NOW - timedelta(hours=ago_h)
    return {"name": name, "path": path, "status": "completed", "conclusion": conclusion,
            "created_at": start.isoformat(), "run_started_at": start.isoformat(),
            "updated_at": (start + timedelta(minutes=minutes)).isoformat()}


RUNS = (
    [run("worker-orchestration-tests", ".github/workflows/worker-orchestration-tests.yml", 9)] * 3
    + [run("youtube-upload", ".github/workflows/youtube-upload.yml", 30)] * 3
    + [run("team-worker", ".github/workflows/team-worker.yml", 4)] * 2
    + [run("comms-watch", ".github/workflows/comms-watch.yml", 1, "failure")] * 3
    + [run("comms-watch", ".github/workflows/comms-watch.yml", 1)]
    + [run("codeql", ".github/workflows/codeql.yml", 6)]
    + [run("old", ".github/workflows/old.yml", 99, ago_h=24 * 9)]
)
HANDOFFS = {"schema_version": 1, "items": [
    {"id": "HO-A", "from": "chatgpt", "to": "grok", "task": "t", "reason_cannot_do": "r", "evidence": "e",
     "status": "open", "created_at": (NOW - timedelta(hours=5)).isoformat(), "updated_at": "x"},
    {"id": "HO-B", "from": "grok", "to": "auditor", "task": "t", "reason_cannot_do": "YAPAMADIM: anahtar yok",
     "evidence": "e", "status": "claimed", "created_at": (NOW - timedelta(hours=1)).isoformat(), "updated_at": "x"},
]}
HEALTH = [
    {"ts": (NOW - timedelta(hours=48)).isoformat(), "providers": [
        {"name": "groq", "status": "no_key"}, {"name": "claude", "status": "billing"}]},
    {"ts": (NOW - timedelta(hours=24)).isoformat(), "providers": [
        {"name": "groq", "status": "no_key"}, {"name": "claude", "status": "ok"}]},
]
PULLS = [{"number": 7, "head": {"ref": "bot/HO-A-1"}, "created_at": (NOW - timedelta(hours=10)).isoformat(),
          "html_url": "u"}, {"number": 8, "head": {"ref": "feature/x"}, "created_at": NOW.isoformat()}]


def report(factory=None, handoffs=None):
    return ib.build_report(now=NOW, runs=RUNS, pulls=PULLS, handoffs=handoffs or copy.deepcopy(HANDOFFS),
                           health_snaps=HEALTH, adapter_factory=factory)


class BottleneckTests(unittest.TestCase):
    def test_ranking(self):
        b = report()["bottlenecks"]
        self.assertEqual([w["workflow"] for w in b["slowest_workflows"]],
                         ["youtube-upload", "worker-orchestration-tests", "codeql"])
        self.assertEqual(b["most_failing_workflow"]["workflow"], "comms-watch")
        self.assertEqual(b["most_failing_workflow"]["failure_rate"], 0.75)
        self.assertEqual(b["longest_open_handoff"]["id"], "HO-A")
        self.assertEqual(b["most_down_provider"]["provider"], "groq")
        self.assertEqual(b["most_down_provider"]["no_key_h"], 48.0)
        self.assertEqual(b["longest_waiting_bot_pr"]["number"], 7)
        self.assertEqual(b["yapamadim_count"], 1)

    def test_publish_payment_excluded_from_suggestions(self):
        r = report()
        targets = " ".join(s["target"] for s in r["suggestions"])
        self.assertNotIn("youtube-upload", targets)
        self.assertEqual(r["ranked_speedups"][0]["target"], ".github/workflows/worker-orchestration-tests.yml")
        for name in ("youtube-upload", "shorts-free-render", "meta-ingest", "shopify-sync", "payout-x"):
            self.assertTrue(ib.is_denylisted(name))
        self.assertFalse(ib.is_denylisted("team-worker"))

    def _plan(self, factory=None, data=None, dry_run=True, now=NOW):
        data = data if data is not None else copy.deepcopy(HANDOFFS)
        r = ib.build_report(now=now, runs=RUNS, pulls=PULLS, handoffs=data, health_snaps=HEALTH,
                            adapter_factory=factory)
        return r, ib.plan_handoff(r, data, dry_run=dry_run)

    def test_rule_based_without_model(self):
        self.assertIsNone(self._plan()[0]["speedup"]["enriched_by"])
        self.assertIsNone(self._plan(lambda: None)[0]["speedup"]["enriched_by"])

        class Down:
            def run(self, job):
                raise CannotDo("YAPAMADIM: tum saglayicilar dustu")
        r, res = self._plan(lambda: Down())
        s = r["speedup"]
        self.assertIsNone(s["enriched_by"])
        self.assertIn("YAPAMADIM", s["model_error"])
        self.assertIn("medyan", res["payload"]["task"])
        self.assertNotIn("_adapter_factory", r)

    def test_model_enrichment(self):
        class Ok:
            provider = "gemini"
            def run(self, job):
                return {"recommendation": "pip cache ekle", "provider": "gemini"}
        r, res = self._plan(lambda: Ok())
        self.assertEqual(r["speedup"]["enriched_by"], "gemini")
        self.assertIn("pip cache ekle", res["payload"]["task"])


class HandoffDispatchTests(unittest.TestCase):
    _plan = BottleneckTests._plan

    def test_daily_key_and_no_repeat_within_7_days(self):
        data = copy.deepcopy(HANDOFFS)
        _, first = self._plan(data=data, dry_run=False)
        self.assertEqual(first["status"], "pending")
        self.assertEqual(first["handoff_id"], "HO-IMP-20261012-slow-worker-orchestration-tests")
        handoff.validate(data)
        item = data["items"][-1]
        self.assertEqual((item["from"], item["to"], item["status"]), ("grok", "auditor", "open"))
        # same day, second run: next suggestion (not the same one)
        _, second = self._plan(data=data, dry_run=False, now=NOW + timedelta(hours=1))
        self.assertEqual(second["handoff_id"], "HO-IMP-20261012-slow-codeql")
        # third run same day: daily cap (2)
        _, third = self._plan(data=data, dry_run=False, now=NOW + timedelta(hours=2))
        self.assertEqual(third["status"], "daily_cap")
        self.assertEqual(len(third["opened_today"]), 2)
        # next day: first two not reopened (7-day dedupe), a new one is chosen
        _, nxt = self._plan(data=data, dry_run=False, now=NOW + timedelta(days=1))
        self.assertTrue(nxt["handoff_id"].startswith("HO-IMP-20261013-"))
        self.assertNotIn("worker-orchestration", nxt["handoff_id"])
        # after 7 days the first suggestion may come back
        self.assertIn("slow-worker-orchestration-tests", ib.recent_keys(data, NOW + timedelta(days=6)))
        self.assertNotIn("slow-worker-orchestration-tests", ib.recent_keys(data, NOW + timedelta(days=8)))
        self.assertEqual(len({i["id"] for i in data["items"]}), len(data["items"]))

    def test_dry_run_does_not_add(self):
        data = copy.deepcopy(HANDOFFS)
        _, res = self._plan(data=data, dry_run=True)
        self.assertEqual(res["status"], "dry_run")
        self.assertEqual(len(data["items"]), 2)

    def test_dispatch_payload(self):
        data = copy.deepcopy(HANDOFFS)
        _, res = self._plan(data=data, dry_run=False)
        p = res["payload"]
        self.assertEqual(set(p), {"handoff_id", "task", "source"})
        self.assertEqual(p["source"], "improvement-bot")
        self.assertEqual(p["handoff_id"], res["handoff_id"])
        api = mock.Mock()
        with mock.patch.object(ib, "REPORT_PATH") as rp:
            rp.read_text.return_value = __import__("json").dumps({"dispatch": res})
            self.assertEqual(ib.cmd_dispatch(api)["status"], "sent")
        api.repository_dispatch.assert_called_once_with("team-work", p)

    def test_dispatch_skips_when_not_pending(self):
        api = mock.Mock()
        with mock.patch.object(ib, "REPORT_PATH") as rp:
            rp.read_text.return_value = '{"dispatch": {"status": "daily_cap"}}'
            self.assertEqual(ib.cmd_dispatch(api)["status"], "skip")
        api.repository_dispatch.assert_not_called()

    def test_markdown_renders(self):
        r, r["dispatch"] = self._plan()
        md = ib.render_md(r)
        self.assertIn("En yavas 3 workflow", md)
        self.assertIn("comms-watch", md)

    def test_workflow_triggers(self):
        wf = (Path(ib.ROOT) / ".github/workflows/improvement-bot.yml").read_text()
        for needle in ("cron: '23 5 * * *'", "workflow_dispatch", "types: [improvement-check]", "dry_run", "actions: write",
                       "git add state/handoffs.json state/improvement_report.json messages/improvement-latest.md"):
            self.assertIn(needle, wf)
        self.assertNotIn("create_pull_request", wf)


class ReenableTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / ".github/workflows").mkdir(parents=True)
        (root / ".github/workflows/sched.yml").write_text("on:\n  schedule:\n    - cron: '0 1 * * *'\n")
        (root / ".github/workflows/manual.yml").write_text("on:\n  schedule:\n    - cron: '0 1 * * *'\n")
        (root / ".github/workflows/push.yml").write_text("on:\n  push:\n")
        self.root = root
        self.api = mock.Mock()
        self.api.workflows.return_value = [
            {"id": 1, "name": "sched", "path": ".github/workflows/sched.yml", "state": "disabled_inactivity"},
            {"id": 2, "name": "manual", "path": ".github/workflows/manual.yml", "state": "disabled_manually"},
            {"id": 3, "name": "push", "path": ".github/workflows/push.yml", "state": "disabled_inactivity"},
            {"id": 4, "name": "ok", "path": ".github/workflows/sched.yml", "state": "active"},
        ]

    def tearDown(self):
        self.tmp.cleanup()

    def test_enables_only_inactive_scheduled(self):
        res = ib.reenable_inactive(self.api, dry_run=False, root=self.root)
        self.api.enable_workflow.assert_called_once_with(1)
        self.assertEqual({r["id"]: r["action"] for r in res}, {1: "enabled", 3: "skipped_no_schedule"})
        self.assertNotIn(2, [r["id"] for r in res])

    def test_dry_run_does_not_enable(self):
        res = ib.reenable_inactive(self.api, dry_run=True, root=self.root)
        self.api.enable_workflow.assert_not_called()
        self.assertEqual(res[0]["action"], "would_enable")


if __name__ == "__main__":
    unittest.main()
