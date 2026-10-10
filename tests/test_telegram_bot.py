import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts import telegram_bot as tb


class FakeHttp:
    def __init__(self, updates):
        self.updates = updates
        self.calls = []

    def __call__(self, url, payload=None, headers=None):
        self.calls.append((url, payload, headers))
        if url.endswith("/getUpdates"):
            return {"ok": True, "result": self.updates}
        return {"ok": True}

    def sent(self):
        return [p for u, p, _ in self.calls if u.endswith("/sendMessage")]


class FakeAdapter:
    def __init__(self, text="Merhaba Furkan"):
        self.text = text
        self.jobs = []

    def run(self, job):
        self.jobs.append(job)
        return {"recommendation": self.text}


def upd(uid, chat, text):
    return {"update_id": uid, "message": {"chat": {"id": chat}, "text": text}}


class TelegramBotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.offset = Path(self.tmp.name) / "telegram_offset.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_token_exits_zero_without_http(self):
        http = FakeHttp([])
        self.assertEqual(tb.run_once(env={}, http=http, offset_path=self.offset), 0)
        self.assertEqual(http.calls, [])

    def test_unset_allowed_replies_chat_id_once_only(self):
        http = FakeHttp([upd(5, 42, "/start"), upd(6, 42, "selam")])
        tb.run_once(env={"TELEGRAM_BOT_TOKEN": "t"}, http=http, offset_path=self.offset)
        sent = http.sent()
        self.assertEqual(len(sent), 1)
        self.assertIn("42", sent[0]["text"])
        self.assertEqual(json.loads(self.offset.read_text())["offset"], 7)

    def test_ignores_other_chats_and_answers_allowed(self):
        adapter = FakeAdapter()
        http = FakeHttp([upd(1, 99, "selam"), upd(2, 42, "selam")])
        tb.run_once(env={"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_ALLOWED_CHAT_ID": "42"}, http=http,
                    adapter_factory=lambda env: adapter, offset_path=self.offset)
        sent = http.sent()
        self.assertEqual([s["chat_id"] for s in sent], ["42"])
        self.assertEqual(sent[0]["text"], "Merhaba Furkan")
        self.assertIn("Türkçe", adapter.jobs[0]["objective"])

    def test_offset_sent_to_get_updates(self):
        tb.save_offset(10, self.offset)
        http = FakeHttp([])
        tb.run_once(env={"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_ALLOWED_CHAT_ID": "1"}, http=http,
                    offset_path=self.offset)
        self.assertEqual(http.calls[0][1]["offset"], 10)

    def test_llm_failure_is_safe(self):
        def boom(env):
            raise RuntimeError("down")
        self.assertIn("ulaşılamadı", tb.handle_text("soru", env={}, adapter_factory=boom))

    def test_gorev_adds_handoff_to_chatgpt(self):
        seen = {}

        def runner(cmd, **kw):
            seen["cmd"] = cmd
            return SimpleNamespace(returncode=0, stdout="{}", stderr="")
        out = tb.handle_text("/gorev raporu güncelle", runner=runner, env={})
        self.assertIn("furkan→chatgpt", out)
        self.assertIn("team-work tetiklenmedi", out)
        cmd = seen["cmd"]
        self.assertEqual(cmd[cmd.index("--from") + 1], "furkan")
        self.assertEqual(cmd[cmd.index("--to") + 1], "chatgpt")

    def test_gorev_sends_team_work_repository_dispatch(self):
        calls = []

        def runner(cmd, **kw):
            return SimpleNamespace(returncode=0, stdout="{}", stderr="")

        def http(url, payload=None, headers=None):
            calls.append((url, payload, headers))
            return {}
        env = {"GITHUB_TOKEN": "tok", "GITHUB_REPOSITORY": "o/r"}
        out = tb.handle_text("/gorev raporu güncelle", runner=runner, env=env, http=http)
        self.assertIn("team-work tetiklendi: TG-", out)
        self.assertEqual(len(calls), 1)
        url, payload, headers = calls[0]
        self.assertEqual(url, "https://api.github.com/repos/o/r/dispatches")
        self.assertEqual(payload["event_type"], "team-work")
        self.assertEqual(payload["client_payload"]["source"], "telegram")
        self.assertTrue(payload["client_payload"]["message_key"].startswith("TG-"))
        self.assertEqual(headers["Authorization"], "Bearer tok")

    def test_gorev_no_dispatch_when_handoff_fails_or_http_errors(self):
        calls = []
        fail = lambda cmd, **kw: SimpleNamespace(returncode=1, stdout="bad", stderr="")  # noqa: E731
        env = {"GITHUB_TOKEN": "tok", "GITHUB_REPOSITORY": "o/r"}
        out = tb.handle_text("/gorev x", runner=fail, env=env, http=lambda *a: calls.append(a) or {})
        self.assertIn("Handoff eklenemedi", out)
        self.assertEqual(calls, [])

        def boom(*a, **k):
            raise OSError("down")
        self.assertIn("tetiklenemedi", tb.dispatch_team_work("TG-1", env=env, http=boom))

    def test_agent_command_with_text_adds_handoff_to_agent(self):
        seen = {}

        def runner(cmd, **kw):
            seen["cmd"] = cmd
            return SimpleNamespace(returncode=0, stdout="{}", stderr="")
        for cmd_name, agent in [("yedek", "backup-supervisor"), ("arastirma", "research-learner"),
                                ("yurutucu", "automation-runner"), ("rapor", "agents-reporter")]:
            tb.handle_text(f"/{cmd_name} şunu incele", runner=runner)
            self.assertEqual(seen["cmd"][seen["cmd"].index("--to") + 1], agent)

    def test_handoff_real_cli_accepts_agent_actors(self):
        path = Path(self.tmp.name) / "handoffs.json"
        out = tb.add_handoff("deneme", receiver="research-learner", file=path)
        self.assertIn("Görev eklendi", out)
        data = json.loads(path.read_text())
        self.assertEqual(data["items"][0]["from"], "furkan")

    def test_agent_command_summarizes_with_llm(self):
        adapter = FakeAdapter("özet")
        self.assertEqual(tb.handle_text("/rapor", adapter_factory=lambda env: adapter), "özet")
        self.assertIn("agents-reporter", adapter.jobs[0]["objective"])

    def test_dispatch_allowlist_blocks_publish_and_payment(self):
        for wf in ("youtube-upload.yml", "meta-bridge-auto.yml", "automation-runner.yml",
                   "shorts-free-build.yml", "payment.yml", "publish.yml"):
            self.assertFalse(tb.is_dispatch_allowed(wf), wf)
        self.assertTrue(tb.is_dispatch_allowed("worker-orchestration-tests.yml"))
        http = FakeHttp([])
        out = tb.dispatch_workflow("youtube-upload.yml", env={"GITHUB_TOKEN": "x", "GITHUB_REPOSITORY": "a/b"},
                                   http=http)
        self.assertIn("tetiklenemez", out)
        self.assertEqual(http.calls, [])

    def test_dispatch_allowed_workflow_calls_api(self):
        http = FakeHttp([])
        out = tb.handle_text("/arastirma calistir", env={"GITHUB_TOKEN": "x", "GITHUB_REPOSITORY": "a/b"}, http=http)
        self.assertIn("tetiklendi", out)
        self.assertTrue(http.calls[0][0].endswith("/workflows/research-learner.yml/dispatches"))
        out = tb.handle_text("/yurutucu calistir", env={"GITHUB_TOKEN": "x", "GITHUB_REPOSITORY": "a/b"}, http=http)
        self.assertIn("tetiklenemez", out)

    def test_every_allowlisted_workflow_exists(self):
        wf_dir = Path(tb.ROOT) / ".github" / "workflows"
        for wf in tb.DISPATCH_ALLOWLIST:
            self.assertTrue((wf_dir / wf).exists(), wf)


if __name__ == "__main__":
    unittest.main()
