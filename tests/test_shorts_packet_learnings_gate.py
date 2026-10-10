"""Render packets must reference and apply the current Shorts learnings (gate fails closed)."""
import copy
import json
import unittest
from unittest.mock import patch

from scripts import shorts_learnings, shorts_research

ROOT = shorts_research.ROOT
MBAPPE = shorts_research.SHORTS / "packets" / "SHORT-CERNO-MBAPPE-001.json"


def packet():
    return copy.deepcopy(json.loads(MBAPPE.read_text(encoding="utf-8")))


@patch("scripts.shorts_research.is_duplicate", return_value=False)
class LearningsGateTests(unittest.TestCase):
    def test_required_ids_mirror_render_rules(self, _d):
        self.assertEqual(set(shorts_research.REQUIRED_LEARNING_IDS), set(shorts_learnings.RULES))

    def test_mbappe_packet_passes_learnings_gate(self, _d):
        self.assertEqual(shorts_research.learnings_blockers(packet()), [])

    def test_missing_learnings_block_fails(self, _d):
        p = packet(); del p["learnings"]
        self.assertIn("learnings_missing", shorts_research.gate_packet(p))

    def test_missing_required_id_fails(self, _d):
        p = packet(); p["learnings"]["learning_ids"].remove("learn_53ca8fb858703eb6")
        self.assertIn("learnings_missing_id_learn_53ca8fb858703eb6", shorts_research.gate_packet(p))

    def test_nonexistent_weekly_note_fails(self, _d):
        p = packet(); p["learnings"]["weekly_note"] = "knowledge/shorts/learnings/weekly-1999-01.md"
        self.assertIn("learnings_weekly_note_missing", shorts_research.gate_packet(p))

    def test_stale_weekly_note_fails(self, _d):
        with patch("scripts.shorts_research.current_weekly_notes",
                   return_value=["knowledge/shorts/learnings/weekly-2099-02.md"]):
            self.assertIn("learnings_weekly_note_stale", shorts_research.gate_packet(packet()))

    def test_success_patterns_must_be_referenced(self, _d):
        p = packet(); p["learnings"]["success_patterns"] = ""
        self.assertIn("learnings_success_patterns_unreferenced", shorts_research.gate_packet(p))

    def test_reference_without_application_fails(self, _d):
        p = packet(); p["learnings"]["applied"] = ["ok"]
        self.assertIn("learnings_not_applied", shorts_research.gate_packet(p))

    def test_legacy_non_render_packet_not_affected(self, _d):
        p = packet(); p.pop("learnings"); p["free_render_requested"] = False
        self.assertNotIn("learnings_missing", shorts_research.gate_packet(p))

    def test_mbappe_packet_is_pipeline_shaped_but_honestly_blocked(self, _d):
        blockers = shorts_research.gate_packet(packet())
        self.assertEqual(sorted(blockers), ["checklist_facts_verified", "checklist_rights_ok", "checklist_sources_reliable"])
        self.assertLessEqual(packet()["target_seconds"], shorts_learnings.MAX_CONCEPT_SECONDS)

    def test_success_patterns_file_cites_official_sources(self, _d):
        text = (ROOT / shorts_research.SUCCESS_PATTERNS).read_text(encoding="utf-8")
        for host in ("support.google.com/youtube", "blog.youtube", "CreatorInsider"):
            self.assertIn(host, text)
        self.assertIn("[SOURCED]", text); self.assertIn("[OBSERVED]", text)


if __name__ == "__main__":
    unittest.main()
