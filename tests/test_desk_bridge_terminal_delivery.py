import unittest

from scripts import desk_bridge as db


class DeskBridgeTerminalDeliveryTests(unittest.TestCase):
    def test_done_source_overrides_stale_delayed_ledger(self):
        block = {"id": "MSG-DONE", "status": "done"}
        existing = {"status": "delayed"}
        self.assertEqual(
            db._desired_status("shared-inbox", block, set(), existing, fresh=False),
            "answered",
        )

    def test_blocked_source_does_not_remain_delayed_when_no_reply_is_expected(self):
        block = {"id": "MSG-BLOCKED", "status": "blocked"}
        existing = {"status": "delayed"}
        self.assertEqual(
            db._desired_status("shared-inbox", block, set(), existing, fresh=False),
            "answered",
        )

    def test_team_report_done_still_waits_for_reader_ack(self):
        block = {"id": "RPT-DONE", "status": "done"}
        self.assertEqual(
            db._desired_status("team-reports", block, set(), {}, fresh=True),
            "pending",
        )

    def test_desk_bridge_health_metadata_uses_hourly_schedule(self):
        body = db._health_body(True, None, {"new_event_keys": []})
        self.assertEqual(body["schedule"], "0 * * * *")
        self.assertIn("next hourly schedule", body["retry"])


if __name__ == "__main__":
    unittest.main()
