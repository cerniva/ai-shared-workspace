import json
import unittest

from scripts import team_worker as tw
from tests.test_team_worker import Base, FakeClient, FakeGit, _ok_factory


class CiBekciHandoffRegistration(Base):
    def _run(self, hid, source, task):
        return tw.process_handoff(hid, run_id="42", client=FakeClient(), env=self.env, root=self.root,
                                  task=task, source=source, adapter_factory=_ok_factory,
                                  test_runner=lambda: (True, "OK"), git_ops=FakeGit(),
                                  now="2026-10-11T13:00:00+00:00")

    def test_ci_bekci_unknown_handoff_is_registered_not_refused(self):
        self._run("CI-38140349974", "ci-bekci", "worker-orchestration-tests failing: fix it")
        data = json.loads((self.root / "state/handoffs.json").read_text())
        item = tw.find_handoff(data, "CI-38140349974")
        self.assertIsNotNone(item)
        self.assertEqual((item["from"], item["to"]), ("auditor", "grok"))
        self.assertEqual(item["status"], "claimed")
        self.assertEqual(item["claimed_by"], "team-worker")
        self.assertTrue(any("team-worker:" in n for n in item["notes"]))

    def test_unknown_handoff_from_other_source_still_refused(self):
        with self.assertRaises(tw.TeamWorkerError):
            self._run("HO-NOPE", "repository_dispatch", "x")

    def test_ci_bekci_without_task_still_refused(self):
        with self.assertRaises(tw.TeamWorkerError):
            self._run("CI-1", "ci-bekci", None)


if __name__ == "__main__":
    unittest.main()
