import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from scripts import comms_watch as cw
from scripts import desk_bridge

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


def item(i, *, minutes, status="open", **extra):
    stamp = (NOW - timedelta(minutes=minutes)).isoformat()
    base = {"id": i, "from": "chatgpt", "to": "grok", "task": "t", "reason_cannot_do": "r", "evidence": "e",
            "status": status, "created_at": stamp, "updated_at": stamp}
    base.update(extra)
    return base


class CommsWatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.handoffs = self.dir / "handoffs.json"
        self.state = self.dir / "comms_watch.json"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, items):
        self.handoffs.write_text(json.dumps({"schema_version": 1, "items": items}), encoding="utf-8")

    def run_cw(self, rows=()):
        return cw.run(handoffs_path=self.handoffs, state_path=self.state, now=NOW, inbox_rows=list(rows))

    def test_handoff_filters(self):
        self.write([
            item("HO-new", minutes=20),
            item("HO-young", minutes=5),
            item("HO-old", minutes=180),
            item("HO-claimed", minutes=30, status="claimed", claimed_at=NOW.isoformat()),
            item("HO-acked", minutes=30, acked_at=NOW.isoformat()),
            item("HO-20261009-03", minutes=30),
            item("HO-20261009-08", minutes=30),
        ])
        out = self.run_cw()
        self.assertEqual(out["alerts"], [{"id": "HO-new", "owner": "grok", "kind": "handoff_unacked",
                                          "age_min": 20, "task": "t"}])

    def test_watch_since_drops_pre_cutoff_messages(self):
        self.write([])
        rows = [
            {"channel": "chatgpt-to-grok", "id": "MSG-old", "created_at": "2026-10-08T23:59:00+03:00", "age_hours": 30},
            {"channel": "shared-inbox", "id": "MSG-naive-old", "created_at": "2026-10-08T12:00:00", "age_hours": 40},
            {"channel": "chatgpt-to-grok", "id": "MSG-new", "created_at": "2026-10-09T00:00:00+03:00", "age_hours": 5},
        ]
        out = self.run_cw(rows)
        self.assertEqual([a["id"] for a in out["alerts"]], ["MSG-new"])
        self.assertEqual(cw.WATCH_SINCE.isoformat(), "2026-10-09T00:00:00+03:00")

    def test_backlog_migration_alerts_but_never_dispatches(self):
        self.write([item("HO-mig", minutes=20, source="backlog-migration"), item("HO-live", minutes=20)])
        out = self.run_cw()
        self.assertEqual(sorted(a["id"] for a in out["alerts"]), ["HO-live", "HO-mig"])
        self.assertEqual([d["client_payload"]["handoff_id"] for d in out["dispatches"]], ["HO-live"])

    def test_inbox_threshold_owner_and_skip(self):
        self.write([])
        rows = [
            {"channel": "chatgpt-to-grok", "id": "MSG-1", "created_at": "x", "age_hours": 0.5},
            {"channel": "shared-inbox", "id": "MSG-2", "created_at": "x", "age_hours": 0.05},
            {"channel": "team-reports", "id": "RPT-1", "created_at": "x", "age_hours": 1.0},
        ]
        out = self.run_cw(rows)
        self.assertEqual([(a["id"], a["owner"], a["kind"], a["age_min"]) for a in out["alerts"]],
                         [("MSG-1", "grok", "inbox_unread", 30), ("RPT-1", "team", "inbox_unread", 60)])
        self.assertEqual(out["dispatches"], [])

    def test_idempotent_state(self):
        self.write([item("HO-new", minutes=20)])
        first = self.run_cw()
        self.assertEqual(len(first["alerts"]), 1)
        second = self.run_cw()
        self.assertEqual(second["alerts"], [])
        self.assertEqual(len(second["active"]), 1)
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertIn("HO-new", saved["alerted"])

    def test_dispatch_payloads(self):
        alerts = [{"id": "HO-a", "owner": "grok", "kind": "handoff_unacked", "age_min": 20, "task": "do x"},
                  {"id": "MSG-1", "owner": "grok", "kind": "inbox_unread", "age_min": 20},
                  {"id": "HO-b", "owner": "grok", "kind": "handoff_unacked", "age_min": 20, "task": "y"}]
        self.assertEqual(cw.dispatch_payloads(alerts, {"HO-b": "x"}), [{"event_type": "team-work",
                         "client_payload": {"handoff_id": "HO-a", "task": "do x", "source": "comms-watch"}}])

    def test_dispatch_once_per_handoff(self):
        self.write([item("HO-new", minutes=20)])
        self.assertEqual(len(self.run_cw()["dispatches"]), 1)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        state["alerted"] = {}
        self.state.write_text(json.dumps(state), encoding="utf-8")
        second = self.run_cw()
        self.assertEqual(len(second["alerts"]), 1)
        self.assertEqual(second["dispatches"], [])

    def test_priority_handoff_from_dispatch_event(self):
        self.write([item("HO-a", minutes=20), item("HO-b", minutes=30)])
        event = self.dir / "event.json"
        event.write_text(json.dumps({"action": "main-merged", "client_payload": {
            "pr_number": 7, "merge_sha": "abc1234", "handoff_id": "HO-b"}}), encoding="utf-8")
        hid = cw.priority_handoff_id(event)
        self.assertEqual(hid, "HO-b")
        self.assertIsNone(cw.priority_handoff_id(self.dir / "missing.json"))
        out = cw.run(handoffs_path=self.handoffs, state_path=self.state, now=NOW, inbox_rows=[], priority_id=hid)
        self.assertEqual(out["active"][0]["id"], "HO-b")
        self.assertEqual(out["priority"], {"id": "HO-b", "found": True, "status": "open", "owner": "grok", "acked": False})
        self.assertEqual(cw.priority_status({"items": []}, "HO-x"), {"id": "HO-x", "found": False})

    def test_corrupt_state_recovers(self):
        self.write([item("HO-new", minutes=20)])
        self.state.write_text("{bad", encoding="utf-8")
        self.assertEqual(len(self.run_cw()["alerts"]), 1)

    def test_real_unread_rows_with_temp_channel(self):
        self.write([])
        inbox = self.dir / "shared-inbox.md"
        created = (desk_bridge.now_tr() - timedelta(minutes=40)).isoformat()
        inbox.write_text(f"---\nid: MSG-T1\nfrom: grok\nto: team\ncreated_at: {created}\n---\nhello\n", encoding="utf-8")
        with mock.patch.dict(desk_bridge.CHANNELS, {"shared-inbox": (inbox, None, "team")}), \
                mock.patch.object(desk_bridge, "INBOX_WATCH_CHANNELS", ("shared-inbox",)), \
                mock.patch.object(desk_bridge, "INBOX_READ_PATH", self.dir / "inbox_read.json"):
            out = cw.run(handoffs_path=self.handoffs, state_path=self.state, now=NOW)
        self.assertEqual([a["id"] for a in out["alerts"]], ["MSG-T1"])
        self.assertGreaterEqual(out["alerts"][0]["age_min"], 39)

    def test_telegram_send_only(self):
        calls = []
        result = {"alerts": [{"id": "HO-new", "owner": "grok", "kind": "handoff_unacked", "age_min": 20}], "active": []}
        self.assertFalse(cw.notify_telegram(result, env={}, http=lambda *a: calls.append(a)))
        self.assertTrue(cw.notify_telegram(result, env={"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_ALLOWED_CHAT_ID": "1"},
                                           http=lambda url, payload=None, headers=None: calls.append(url) or {}))
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].endswith("/sendMessage"))

    # --- ChatGPT triggers ---
    def chatgpt_run(self, *, event_name=None, event=None, msgs=None):
        self.write([])
        return cw.run(handoffs_path=self.handoffs, state_path=self.state, now=NOW, inbox_rows=[],
                      event_name=event_name, event=event, chatgpt_messages_path=msgs or (self.dir / "c2g.md"))

    def push_event(self, ref="refs/heads/chatgpt/fix-1", sha="a" * 40, message="work"):
        return {"ref": ref, "after": sha, "deleted": False, "head_commit": {"message": message}}

    def test_chatgpt_branch_push_dispatch_and_idempotent(self):
        out = self.chatgpt_run(event_name="push", event=self.push_event())
        self.assertEqual([d["client_payload"] for d in out["dispatches"]],
                         [{"source": "chatgpt", "branch": "chatgpt/fix-1", "sha": "a" * 40}])
        self.assertEqual(out["dispatches"][0]["event_type"], "team-work")
        again = self.chatgpt_run(event_name="push", event=self.push_event())
        self.assertEqual(again["dispatches"], [])
        newer = self.chatgpt_run(event_name="push", event=self.push_event(sha="b" * 40))
        self.assertEqual(len(newer["dispatches"]), 1)
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertIn("chatgpt/fix-1@" + "a" * 40, saved["chatgpt_branches"])

    def test_chatgpt_branch_ignored_cases(self):
        self.assertIsNone(cw.chatgpt_branch_from_event("push", self.push_event(ref="refs/heads/main")))
        self.assertIsNone(cw.chatgpt_branch_from_event("schedule", self.push_event()))
        self.assertIsNone(cw.chatgpt_branch_from_event("push", self.push_event(sha="0" * 40)))
        self.assertIsNone(cw.chatgpt_branch_from_event("push", self.push_event(message="x\nsource: backlog-migration")))
        self.assertEqual(cw.chatgpt_branch_from_event("push", self.push_event(ref="refs/heads/chatgpt/a/b")),
                         {"branch": "chatgpt/a/b", "sha": "a" * 40})

    def test_chatgpt_message_append_dispatch_and_idempotent(self):
        msgs = self.dir / "c2g.md"
        block = "---\nid: {i}\nfrom: chatgpt\nto: grok\n{extra}---\n\nbody {i}\n\n"
        msgs.write_text("# ChatGPT -> Grok\n\n" + block.format(i="MSG-1", extra=""), encoding="utf-8")
        first = self.chatgpt_run(msgs=msgs)  # baseline: existing backlog is not dispatched
        self.assertEqual(first["dispatches"], [])
        with msgs.open("a", encoding="utf-8") as fh:
            fh.write(block.format(i="MSG-2", extra=""))
            fh.write(block.format(i="MSG-3", extra="source: backlog-migration\n"))
        out = self.chatgpt_run(msgs=msgs)
        self.assertEqual([d["client_payload"] for d in out["dispatches"]],
                         [{"source": "chatgpt", "path": "messages/chatgpt-to-grok.md", "message_id": "MSG-2"}])
        self.assertEqual(self.chatgpt_run(msgs=msgs)["dispatches"], [])
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertIn("MSG-2", saved["chatgpt_messages"])

    def test_chatgpt_message_without_id_uses_line_hash(self):
        parsed = cw.parse_chatgpt_messages("---\nid:\nfrom: chatgpt\n---\nhi\n")
        self.assertEqual(len(parsed), 1)
        out = cw.chatgpt_message_dispatches(parsed, {})
        self.assertEqual(set(out[0]["client_payload"]), {"source", "path", "line_hash"})
        self.assertEqual(cw.chatgpt_message_dispatches(parsed, {parsed[0]["key"]: "x"}), [])

    def test_real_chatgpt_file_parses(self):
        parsed = cw.parse_chatgpt_messages((ROOT / "messages/chatgpt-to-grok.md").read_text(encoding="utf-8"))
        self.assertTrue(parsed)
        # ChatGPT desk file may carry MSG- messages and RPT- report blocks (desk_bridge treats RPT- as team-reports).
        self.assertTrue(all(p["message_id"].startswith(("MSG-", "RPT-")) for p in parsed))

    def test_telegram_handoff_not_redispatched(self):
        self.write([item("TG-20261010-010000", minutes=20), item("HO-live", minutes=20)])
        out = self.run_cw()
        self.assertEqual(sorted(a["id"] for a in out["alerts"]), ["HO-live", "TG-20261010-010000"])
        self.assertEqual([d["client_payload"]["handoff_id"] for d in out["dispatches"]], ["HO-live"])

    def test_workflow_chatgpt_triggers(self):
        text = (ROOT / ".github/workflows/comms-watch.yml").read_text(encoding="utf-8")
        self.assertIn('"chatgpt/**"', text)
        self.assertIn("messages/chatgpt-to-grok.md", text)
        self.assertIn("refs/heads/chatgpt/", text)

    def test_workflow_safety(self):
        text = (ROOT / ".github/workflows/comms-watch.yml").read_text(encoding="utf-8")
        self.assertIn("contents: write", text)  # only for repository_dispatch
        self.assertIn("issues: write", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("event_type", text)
        self.assertIn("comms-watch: bekleyen devir/mesaj", text)
        self.assertIn('"17 * * * *"', text)
        self.assertIn("types: [main-merged, team-pr-opened]", text)
        for banned in ("youtube-upload", "git push", "workflow_run", "createWorkflowDispatch", "/actions/workflows/"):
            self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main()
