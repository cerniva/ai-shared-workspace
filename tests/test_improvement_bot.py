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
        self.assertEqual(r["speedup"]["target"], ".github/workflows/worker-orchestration-tests.yml")
        for name in ("youtube-upload", "shorts-free-render", "meta-ingest", "shopify-sync", "payout-x"):
            self.assertTrue(ib.is_denylisted(name))
        self.assertFalse(ib.is_denylisted("team-worker"))

    def test_rule_based_without_model(self):
        self.assertIsNone(report()["speedup"]["enriched_by"])
        self.assertIsNone(report(lambda: None)["speedup"]["enriched_by"])

        class Down:
            def run(self, job):
                raise CannotDo("YAPAMADIM: tum saglayicilar dustu")
        s = report(lambda: Down())["speedup"]
        self.assertIsNone(s["enriched_by"])
        self.assertIn("YAPAMADIM", s["model_error"])
        self.assertIn("medyan", ib.dispatch_payload("HO-X", s)["task"])

    def test_model_enrichment(self):
        class Ok:
            provider = "gemini"
            def run(self, job):
                return {"recommendation": "pip cache ekle", "provider": "gemini"}
        s = report(lambda: Ok())["speedup"]
        self.assertEqual(s["enriched_by"], "gemini")
        self.assertIn("pip cache ekle", ib.dispatch_payload("HO-X", s)["task"])


class HandoffDispatchTests(unittest.TestCase):
    def test_idempotent_week(self):
        data = copy.deepcopy(HANDOFFS)
        r = report(handoffs=data)
        first = ib.plan_handoff(r, data, dry_run=False)
        self.assertEqual(first["status"], "pending")
        self.assertTrue(first["handoff_id"].startswith("HO-IMP-2026W42-"))
        handoff.validate(data)
        item = data["items"][-1]
        self.assertEqual((item["from"], item["to"], item["status"]), ("grok", "auditor", "open"))
        second = ib.plan_handoff(report(handoffs=data), data, dry_run=False)
        self.assertEqual(second, {"status": "already_this_week", "handoff_id": first["handoff_id"]})
        self.assertEqual(sum(i["id"].startswith("HO-IMP-") for i in data["items"]), 1)

    def test_dry_run_does_not_add(self):
        data = copy.deepcopy(HANDOFFS)
        res = ib.plan_handoff(report(handoffs=data), data, dry_run=True)
        self.assertEqual(res["status"], "dry_run")
        self.assertEqual(len(data["items"]), 2)

    def test_dispatch_payload(self):
        data = copy.deepcopy(HANDOFFS)
        res = ib.plan_handoff(report(handoffs=data), data, dry_run=False)
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
            rp.read_text.return_value = '{"dispatch": {"status": "already_this_week"}}'
            self.assertEqual(ib.cmd_dispatch(api)["status"], "skip")
        api.repository_dispatch.assert_not_called()

    def test_markdown_renders(self):
        r = report()
        r["dispatch"] = {"status": "dry_run", "handoff_id": "HO-IMP-2026W42-x"}
        md = ib.render_md(r)
        self.assertIn("En yavas 3 workflow", md)
        self.assertIn("comms-watch", md)

    def test_workflow_triggers(self):
        wf = (Path(ib.ROOT) / ".github/workflows/improvement-bot.yml").read_text()
        for needle in ("cron: '23 6 * * 1'", "workflow_dispatch", "dry_run", "actions: read",
                       "git add state/handoffs.json state/improvement_report.json messages/improvement-latest.md"):
            self.assertIn(needle, wf)
        self.assertNotIn("create_pull_request", wf)


if __name__ == "__main__":
    unittest.main()
