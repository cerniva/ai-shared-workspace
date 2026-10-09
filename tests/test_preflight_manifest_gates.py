"""Flag-only production gates must not pass preflight without review evidence (HO-11)."""
import unittest

from scripts.shorts_preflight import MANIFEST_GATE_REVIEW_CHECKS, manifest_gate_blockers

ALL = {"hook_storyboard_qc_required": True, "rights_qc_required": True,
       "full_mp4_qc_required": True, "moving_footage_only": True}


def review(**checks):
    return {"sha256": "x", "reviewer": "r", "checks": checks}


class ManifestGateTests(unittest.TestCase):
    def test_no_manifest_is_backward_compatible(self):
        self.assertEqual(manifest_gate_blockers(None, None), [])

    def test_flags_without_review_block_every_gate(self):
        blockers = manifest_gate_blockers({"production_gates": ALL}, None)
        for gate in ALL:
            self.assertTrue(any(b.startswith("gate_" + gate) for b in blockers), gate)

    def test_partial_review_still_blocks_hook_storyboard(self):
        r = review(rights_checked=True, speech_intelligible=True, audio_visual_sync=True,
                   text_readable=True, moving_footage_checked=True)
        self.assertEqual(manifest_gate_blockers({"production_gates": ALL}, r),
                         ["gate_hook_storyboard_qc_required_hook_storyboard_checked"])

    def test_truthy_non_bool_is_not_evidence(self):
        keys = {k for v in MANIFEST_GATE_REVIEW_CHECKS.values() for k in v}
        r = review(**{k: "yes" for k in keys})
        self.assertEqual(len(manifest_gate_blockers({"production_gates": ALL}, r)), len(keys))

    def test_full_evidence_passes(self):
        keys = {k for v in MANIFEST_GATE_REVIEW_CHECKS.values() for k in v}
        self.assertEqual(manifest_gate_blockers({"production_gates": ALL}, review(**{k: True for k in keys})), [])

    def test_bad_manifest_shape_blocks(self):
        self.assertEqual(manifest_gate_blockers({"production_gates": "on"}, None), ["manifest_gates_invalid"])


if __name__ == "__main__":
    unittest.main()
