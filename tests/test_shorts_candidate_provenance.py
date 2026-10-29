"""Read-only candidate provenance regression gates; not independent rights approval.

These tests never infer license grants from a metadata file or create media.
"""
from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "knowledge" / "shorts" / "source_candidates"


class CandidateProvenanceTests(unittest.TestCase):
    def _pending_records(self):
        for path in sorted(CANDIDATES.glob("*_rights_pending.json")):
            with self.subTest(candidate=path.name):
                yield path, json.loads(path.read_text(encoding="utf-8"))

    def test_caption_hash_bound_to_actual_candidate_bytes(self):
        for record_path, record in self._pending_records():
            with self.subTest(record=record_path.name):
                # A research-only candidate may have no transcript yet.
                # Never invent an SRT or waive the publication gate.
                if not record.get("caption_path"):
                    self.assertTrue(
                        str(record.get("transcript_status", "")).startswith("TRANSCRIPT_BLOCKED"),
                        "missing captions must explicitly block transcript clearance",
                    )
                    self.assertIs(record.get("publish_ready"), False)
                    self.assertIsNone(record.get("rendered_mp4"))
                    self.assertRegex(record["source_media_sha256"], r"^[0-9a-f]{64}$")
                    continue
                relative = Path(record["caption_path"])
                self.assertFalse(relative.is_absolute())
                self.assertNotIn("..", relative.parts)
                caption_file = ROOT / relative
                self.assertTrue(caption_file.is_file(), str(caption_file))
                actual = hashlib.sha256(caption_file.read_bytes()).hexdigest()
                self.assertEqual(actual, record["caption_sha256"])
                self.assertRegex(record["source_sha256"], r"^[0-9a-f]{64}$")

    def test_unresolved_rights_or_qc_never_claim_publish_ready(self):
        for record_path, record in self._pending_records():
            with self.subTest(record=record_path.name):
                gates = record.get("gates", {})
                blocked = (
                    record.get("status", "").endswith("_BLOCKED")
                    or record.get("source_audio_rights_verified") is False
                    or record.get("source_third_party_music_verified") is False
                    or any(
                        isinstance(value, str) and value.endswith("_BLOCKED")
                        for value in gates.values()
                    )
                )
                if blocked:
                    self.assertIs(record.get("publish_ready"), False)
                    self.assertIs(record.get("real_mp4_exists"), False)
                readability = record.get("caption_readability") or {}
                if readability.get("over_limit_count", 0) > 0:
                    self.assertEqual(
                        record.get("gates", {}).get("caption_readability"),
                        "TRANSCRIPT_BLOCKED",
                    )


if __name__ == "__main__":
    unittest.main()
