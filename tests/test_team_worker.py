import json
import tempfile
import unittest
from pathlib import Path

from scripts import team_worker as tw
from scripts.team_research import research
from scripts.worker_adapters import MissingCredential, RetryableProviderError


class FakeClient:
    def __init__(self, open_pulls=None, fail_pr=False):
        self.open_pulls = open_pulls or []
        self.fail_pr = fail_pr
        self.created, self.issues, self.dispatches = [], [], []

    def list_open_pulls(self):
        return self.open_pulls

    def create_pull(self, **kw):
        if self.fail_pr:
            raise tw.TeamWorkerError("GitHub API POST /pulls -> 403")
        self.created.append(kw)
        n = len(self.created)
        return {"html_url": f"https://github.com/x/y/pull/{n}", "number": n, "head": {"sha": "abc123"}}

    def create_issue(self, **kw):
        self.issues.append(kw)
        return {"html_url": "https://github.com/x/y/issues/1"}

    def repository_dispatch(self, event_type, client_payload):
        tw.assert_workflow_allowed(event_type)
        self.dispatches.append((event_type, client_payload))


class FakeGit:
    def __init__(self, extra_paths=()):
        self.extra = list(extra_paths)
        self.branch = self.pushed = self.committed = None

    def checkout_new(self, branch):
        tw.assert_push_target(branch)
        self.branch = branch

    def changed_paths(self):
        return ["state/handoffs.json", *self.extra]

    def commit(self, msg):
        self.committed = msg

    def push(self, branch):
        tw.assert_push_target(branch)
        self.pushed = branch


class OkAdapter:
    def run(self, job):
        return {"provider": "mock", "model": "m", "recommendation": "do X", "factual_findings": ["a"], "next_action": "n"}


def _ok_factory(env):
    return OkAdapter()


def _missing_factory(env):
    raise MissingCredential("no AI provider credential is configured")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "state").mkdir()
        (self.root / "state/handoffs.json").write_text(json.dumps({"schema_version": 1, "items": [
            {"id": "HO-T-1", "from": "chatgpt", "to": "grok", "task": "do a thing", "status": "open", "notes": []},
            {"id": "HO-T-2", "from": "chatgpt", "to": "auditor", "task": "other", "status": "open"},
        ]}))
        self.env = {"XAI_API_KEY": "xai-secretval12", "GITHUB_TOKEN": "ghs_tokentokentoken"}

    def tearDown(self):
        self.tmp.cleanup()

    def notes(self):
        data = json.loads((self.root / "state/handoffs.json").read_text())
        return tw.find_handoff(data, "HO-T-1")["notes"]

    def run_ho(self, client, git=None, factory=_ok_factory, tests=(True, "OK"), dry=False):
        return tw.process_handoff("HO-T-1", run_id="99", client=client, env=self.env, root=self.root,
                                  adapter_factory=factory, test_runner=lambda: tests,
                                  git_ops=git or FakeGit(), dry_run=dry, now="2026-10-10T00:00:00+00:00")


class MainPushRefusal(Base):
    def test_push_to_main_refused(self):
        for ref in ("main", "refs/heads/main", "HEAD:main", "master", "feature/x"):
            with self.assertRaises(tw.PushRefused):
                tw.assert_push_target(ref)
            with self.assertRaises(tw.PushRefused):
                tw.git_push_branch(ref)  # refused before git is invoked

    def test_bot_branch_shape(self):
        self.assertEqual(tw.bot_branch("HO-1", "42"), "bot/HO-1-42")
        tw.assert_push_target("bot/HO-1-42")
        with self.assertRaises(tw.TeamWorkerError):
            tw.bot_branch("../main", "1")


class Denylist(Base):
    def test_workflow_denylist(self):
        for wf in ("youtube-upload.yml", "shorts-free-render.yml", "shorts-free-publish", "meta-bridge-auto.yml",
                   "shopify-sync", "gumroad", "whop-x", "payment-run", "payout-report"):
            with self.assertRaises(tw.DenylistViolation):
                tw.assert_workflow_allowed(wf)
        tw.assert_workflow_allowed("team-research")
        tw.assert_workflow_allowed("shorts-free-build.yml")

    def test_diff_touching_denylist_rejected_no_pr(self):
        client = FakeClient()
        git = FakeGit([".github/workflows/youtube-upload.yml"])
        with self.assertRaises(tw.DenylistViolation):
            self.run_ho(client, git)
        self.assertEqual(client.created, [])
        self.assertIsNone(git.pushed)


class NoKeyYapamadim(Base):
    def test_missing_key_opens_yapamadim_pr_and_dispatches_research(self):
        client, git = FakeClient(), FakeGit()
        out = self.run_ho(client, git, factory=_missing_factory)
        self.assertEqual(out["status"], "pr")
        self.assertEqual(git.pushed, "bot/HO-T-1-99")
        self.assertIn("YAPAMADIM", client.created[0]["title"])
        self.assertIn("YAPAMADIM", client.created[0]["body"])
        self.assertTrue(any("YAPAMADIM: model anahtari yok" in n for n in self.notes()))
        self.assertEqual(client.dispatches[0][0], "team-research")
        self.assertEqual(set(client.dispatches[0][1]), {"handoff_id", "reason", "task"})
        self.assertEqual(client.dispatches[0][1]["handoff_id"], "HO-T-1")
        self.assertEqual(client.dispatches[1][0], "team-pr-opened")

    def test_model_no_answer_is_yapamadim(self):
        class Dead:
            def run(self, job):
                raise RetryableProviderError("provider network error")
        client = FakeClient()
        self.run_ho(client, factory=lambda env: Dead())
        self.assertTrue(any("model cevap vermedi" in n for n in self.notes()))
        self.assertEqual(len([d for d in client.dispatches if d[0] == "team-research"]), 1)

    def test_pr_failure_falls_back_to_issue(self):
        client = FakeClient(fail_pr=True)
        out = self.run_ho(client, factory=_missing_factory)
        self.assertEqual(out["status"], "issue")
        self.assertIn("YAPAMADIM", client.issues[0]["title"])

    def test_research_dispatched_once(self):
        client = FakeClient()
        item = {"notes": ["x team-worker: YAPAMADIM: y | team-research dispatched (team-research)"]}
        self.assertFalse(tw.trigger_research(client, item, "HO-T-1", "r", "t"))
        self.assertEqual(client.dispatches, [])

    def test_success_path_no_research_dispatch(self):
        client = FakeClient()
        out = self.run_ho(client)
        self.assertEqual(out["status"], "pr")
        self.assertFalse(out["draft"])
        self.assertEqual([d for d in client.dispatches if d[0] == "team-research"], [])
        self.assertTrue((self.root / "state/team_work/HO-T-1.json").exists())

    def test_secret_never_in_output(self):
        def leaky(env):
            raise MissingCredential("bad key " + env["XAI_API_KEY"])
        client = FakeClient()
        self.run_ho(client, factory=leaky)
        blob = json.dumps([client.created, client.dispatches, self.notes()])
        self.assertNotIn("xai-secretval12", blob)


class RedTestsDraft(Base):
    def test_red_tests_open_draft_with_reason(self):
        client = FakeClient()
        out = self.run_ho(client, tests=(False, "FAILED (failures=1)"))
        self.assertTrue(out["draft"])
        self.assertTrue(client.created[0]["draft"])
        self.assertIn("FAILED (failures=1)", client.created[0]["body"])


class Idempotent(Base):
    def test_open_pr_blocks_new_one(self):
        client = FakeClient(open_pulls=[{"number": 7, "html_url": "u7", "head": {"ref": "bot/HO-T-1-55"}}])
        git = FakeGit()
        out = self.run_ho(client, git, factory=_missing_factory)
        self.assertEqual(out["status"], "exists")
        self.assertEqual(client.created, [])
        self.assertEqual(client.dispatches, [])
        self.assertIsNone(git.branch)

    def test_other_handoff_pr_does_not_block(self):
        client = FakeClient(open_pulls=[{"head": {"ref": "bot/HO-T-10-1"}}])
        self.assertIsNone(tw.find_open_pr(client, "HO-T-1"))

    def test_dry_run_no_push_no_pr_no_dispatch(self):
        client, git = FakeClient(), FakeGit()
        out = self.run_ho(client, git, factory=_missing_factory, dry=True)
        self.assertEqual(out["status"], "dry_run")
        self.assertIsNone(git.pushed)
        self.assertEqual((client.created, client.dispatches), ([], []))


class Targets(Base):
    def test_resolve_targets(self):
        data = json.loads((self.root / "state/handoffs.json").read_text())
        self.assertEqual(tw.resolve_targets("repository_dispatch",
                         {"client_payload": {"handoff_id": "HO-T-1", "task": "t", "source": "bridge"}}, None, data),
                         [("HO-T-1", "t", "bridge")])
        self.assertEqual(tw.resolve_targets("push", {}, None, data), [("HO-T-1", None, "push")])
        with self.assertRaises(tw.TeamWorkerError):
            tw.resolve_targets("repository_dispatch", {"client_payload": {}}, None, data)


class AutoMergeGateCompat(Base):
    def cfg(self):
        return json.loads(Path("config/auto_merge.json").read_text())

    def _research(self, client):
        return [d for d in client.dispatches if d[0] == "team-research"]

    def test_green_body_has_ho_and_evidence_and_bot_prefix(self):
        import re
        client, git = FakeClient(), FakeGit()
        tw_data = json.loads((self.root / "state/handoffs.json").read_text())
        tw_data["items"][0]["id"] = "HO-20261010-99"
        (self.root / "state/handoffs.json").write_text(json.dumps(tw_data))
        tw.process_handoff("HO-20261010-99", run_id="7", client=client, env=self.env, root=self.root,
                           adapter_factory=_ok_factory, test_runner=lambda: (True, "OK"), git_ops=git)
        body, cfg = client.created[0]["body"], self.cfg()
        self.assertTrue(any(git.pushed.startswith(p) for p in cfg["allowed_head_prefixes"]))
        self.assertEqual(re.search(cfg["handoff_regex"], body).group(0), "HO-20261010-99")
        self.assertRegex(body, cfg["evidence_regex"])
        self.assertIn("\nTest: geçti", body)
        self.assertFalse(client.created[0]["draft"])

    def test_red_body_draft_without_evidence_line(self):
        import re
        client = FakeClient()
        self.run_ho(client, tests=(False, "FAILED (errors=2)"))
        body = client.created[0]["body"]
        self.assertTrue(client.created[0]["draft"])
        self.assertIsNone(re.search(self.cfg()["evidence_regex"], body))
        self.assertNotRegex(body, r"(?m)^\s*(Test|CI)\s*:")

    def test_non_ho_id_writes_handoff_yok(self):
        body = tw.build_pr_body(handoff_id="TASK-5", source="s", run_id="1", task="t", failure=None,
                                result={"recommendation": "r"}, tests_ok=True, test_tail="", test_cmd="c", run_url="")
        self.assertIn("handoff: yok", body)
        self.assertNotIn("HO-yok", body)
        self.assertEqual(tw.handoff_line("HO-20261010-1"), "Handoff: HO-20261010-1")

    def test_pr_opened_dispatch_payload(self):
        client = FakeClient()
        self.run_ho(client)
        opened = [d for d in client.dispatches if d[0] == "team-pr-opened"]
        self.assertEqual(opened, [("team-pr-opened", {"pr_number": 1, "head_sha": "abc123", "handoff_id": "HO-T-1"})])
        self.assertEqual(self._research(client), [])

    def test_no_pr_no_pr_opened_dispatch(self):
        client = FakeClient(fail_pr=True)
        self.run_ho(client)
        self.assertEqual([d for d in client.dispatches if d[0] == "team-pr-opened"], [])

    def test_default_factory_uses_model_fallback(self):
        from unittest import mock
        with mock.patch("scripts.model_fallback.fallback_adapter", return_value=None) as fb:
            with self.assertRaises(MissingCredential):
                tw.default_adapter_factory({})
            fb.assert_called_once()
        sentinel = OkAdapter()
        with mock.patch("scripts.model_fallback.fallback_adapter", return_value=sentinel):
            self.assertIs(tw.default_adapter_factory({}), sentinel)

    def test_cannot_do_dispatches_research_and_provider_check(self):
        from scripts.model_fallback import CannotDo

        class Chain:
            def run(self, job):
                raise CannotDo("YAPAMADIM: all providers failed")
        client = FakeClient()
        self.run_ho(client, factory=lambda env: Chain())
        kinds = [d[0] for d in client.dispatches]
        self.assertIn("team-research", kinds)
        self.assertIn("provider-check", kinds)
        self.assertTrue(any("YAPAMADIM: model cevap vermedi (CannotDo" in n for n in self.notes()))

    def test_no_key_no_provider_check(self):
        client = FakeClient()
        self.run_ho(client, factory=_missing_factory)
        self.assertNotIn("provider-check", [d[0] for d in client.dispatches])


class PushBatchSafety(unittest.TestCase):
    def data(self):
        return {"items": [
            {"id": "HO-B", "to": "grok", "status": "open", "created_at": "2026-10-10T02:00:00+00:00"},
            {"id": "HO-A", "to": "worker", "status": "open", "created_at": "2026-10-10T01:00:00+00:00"},
            {"id": "HO-C", "to": "grok", "status": "open", "created_at": "2026-10-10T03:00:00+00:00"},
            {"id": "HO-M1", "to": "grok", "status": "open", "source": "backlog-migration", "created_at": "2026-01-01T00:00:00+00:00"},
            {"id": "HO-M2", "to": "grok", "status": "open", "notes": ["x Migrated from old board"], "created_at": "2026-01-01T00:00:00+00:00"},
        ]}

    def test_push_starts_only_oldest_one(self):
        self.assertEqual(tw.resolve_targets("push", {}, None, self.data()), [("HO-A", None, "push")])
        self.assertEqual(tw.pending_worker_handoffs(self.data()), ["HO-A", "HO-B", "HO-C"])

    def test_migrated_never_auto_picked_but_dispatchable(self):
        only_migrated = {"items": [i for i in self.data()["items"] if i["id"].startswith("HO-M")]}
        self.assertEqual(tw.resolve_targets("push", {}, None, only_migrated), [])
        self.assertEqual(tw.resolve_targets("repository_dispatch", {"client_payload": {"handoff_id": "HO-M1"}}, None, only_migrated),
                         [("HO-M1", None, "repository_dispatch")])
        self.assertEqual(tw.resolve_targets("workflow_dispatch", {"inputs": {"handoff_id": "HO-M2"}}, None, only_migrated),
                         [("HO-M2", None, "workflow_dispatch")])


class TeamResearch(Base):
    def test_research_appends_note_once(self):
        path = self.root / "state/handoffs.json"
        payload = {"handoff_id": "HO-T-1", "reason": "no key", "task": "t"}
        self.assertEqual(research(payload, adapter=OkAdapter(), handoffs=path, env={}), "noted")
        self.assertEqual(research(payload, adapter=OkAdapter(), handoffs=path, env={}), "already_noted")
        self.assertEqual(sum("research-learner (team-research)" in n for n in self.notes()), 1)

    def test_research_without_key_still_notes(self):
        path = self.root / "state/handoffs.json"
        research({"handoff_id": "HO-T-1", "reason": "r", "task": "t"}, adapter=None, handoffs=path, env={})
        self.assertTrue(any("model anahtari yok" in n for n in self.notes()))


class WorkflowWiring(unittest.TestCase):
    def test_workflow_triggers(self):
        wf = Path(".github/workflows/team-worker.yml").read_text()
        for needle in ("types: [team-work]", "handoff_id", "dry_run", "state/handoffs.json",
                       "cancel-in-progress: false", "python3 -m scripts.team_worker"):
            self.assertIn(needle, wf)
        rl = Path(".github/workflows/research-learner.yml").read_text()
        self.assertIn("types: [team-research]", rl)
        self.assertIn("python3 -m scripts.team_research", rl)


if __name__ == "__main__":
    unittest.main()
