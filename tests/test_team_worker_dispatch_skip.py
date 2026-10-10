import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import team_worker as tw


class RepositoryDispatchWithoutHandoffId(unittest.TestCase):
    """comms-watch ChatGPT notices (no handoff_id) must not turn team-worker red."""

    def _run(self, payload):
        with tempfile.TemporaryDirectory() as d:
            ev = Path(d) / "event.json"
            ev.write_text(json.dumps({"client_payload": payload}))
            env = {"GITHUB_EVENT_NAME": "repository_dispatch", "GITHUB_EVENT_PATH": str(ev)}
            with mock.patch.dict(os.environ, env), \
                    mock.patch.object(tw, "load_handoffs", return_value={"items": []}), \
                    mock.patch.object(tw, "GitHubClient", side_effect=AssertionError("no API call expected")), \
                    mock.patch.object(tw, "with_queue", side_effect=AssertionError("queue must not be used")):
                return tw.main([])

    def test_chatgpt_branch_notice_skipped(self):
        self.assertEqual(self._run({"source": "chatgpt", "branch": "chatgpt/x-20261010", "sha": "abc123"}), 0)

    def test_chatgpt_message_notice_skipped(self):
        self.assertEqual(self._run({"source": "chatgpt", "path": "messages/chatgpt-to-grok.md", "message_id": "m1"}), 0)

    def test_resolve_targets_still_strict(self):
        with self.assertRaises(tw.TeamWorkerError):
            tw.resolve_targets("repository_dispatch", {"client_payload": {}}, None, {"items": []})


if __name__ == "__main__":
    unittest.main()
