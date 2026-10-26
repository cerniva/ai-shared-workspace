"""Sourced upload credits and independent-review binding (no network/upload)."""
import copy
import unittest
from scripts.youtube_upload import require_content_rights_metadata


class SourcedAttributionGateTests(unittest.TestCase):
    def setUp(self):
        self.hash_source = "a" * 64
        self.hash_captions = "b" * 64
        self.rights = {
            "source_url": "https://example.org/source",
            "license_url": "https://example.org/source-license",
            "license_name": "Fixture license",
            "caption_source_url": "https://example.org/captions",
            "caption_license_url": "https://example.org/caption-license",
            "caption_license_name": "Fixture caption license",
            "caption_attribution_text": "Captions by Fixture Author",
            "changes_notice": "Edited to 9:16, English subtitles burned in",
            "source_sha256": self.hash_source,
            "captions_sha256": self.hash_captions,
            "reuse_permitted": True,
            "derivatives_permitted": True,
            "audio_reuse_permitted": True,
            "caption_reuse_permitted": True,
            "caption_derivatives_permitted": True,
        }
        self.preflight = {
            "source_sha256": self.hash_source,
            "captions_sha256": self.hash_captions,
            "independent_rights_review": True,
            "independent_media_review": True,
            "spoken_caption_sync_review": True,
            "framing_review": True,
        }
        description = "\n".join([
            self.rights[k] for k in ("source_url", "license_url",
                                     "caption_source_url", "caption_license_url",
                                     "caption_attribution_text", "changes_notice")
        ])
        self.meta = {"content_origin": "sourced", "source_rights": self.rights,
                     "description": description}

    def test_sourced_complete_evidence_passes_metadata_gate_only(self):
        self.assertIsNone(require_content_rights_metadata(self.meta, self.preflight))

    def test_missing_origin_cannot_bypass_sourced_gate(self):
        self.meta.pop("content_origin")
        with self.assertRaisesRegex(ValueError, "content_origin"):
            require_content_rights_metadata(self.meta, self.preflight)

    def test_explicit_original_has_no_sourced_credit_requirement(self):
        self.meta = {"content_origin": "original", "description": "My own content"}
        self.assertIsNone(require_content_rights_metadata(self.meta, {}))

    def test_missing_caption_license_blocks(self):
        self.rights.pop("caption_license_url")
        with self.assertRaisesRegex(ValueError, "caption_license_url"):
            require_content_rights_metadata(self.meta, self.preflight)

    def test_missing_audio_reuse_permission_blocks(self):
        self.rights["audio_reuse_permitted"] = False
        with self.assertRaisesRegex(ValueError, "audio_reuse_permitted"):
            require_content_rights_metadata(self.meta, self.preflight)

    def test_unbound_caption_hash_blocks(self):
        self.preflight["captions_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "not bound"):
            require_content_rights_metadata(self.meta, self.preflight)

    def test_missing_independent_rights_review_blocks(self):
        self.preflight["independent_rights_review"] = False
        with self.assertRaisesRegex(ValueError, "independent_rights_review"):
            require_content_rights_metadata(self.meta, self.preflight)

    def test_missing_spoken_sync_review_blocks(self):
        self.preflight.pop("spoken_caption_sync_review")
        with self.assertRaisesRegex(ValueError, "spoken_caption_sync_review"):
            require_content_rights_metadata(self.meta, self.preflight)

    def test_missing_description_attribution_blocks(self):
        self.meta["description"] = self.meta["description"].replace(
            self.rights["caption_attribution_text"], ""
        )
        with self.assertRaisesRegex(ValueError, "caption_attribution_text"):
            require_content_rights_metadata(self.meta, self.preflight)

    def test_missing_change_notice_blocks(self):
        self.meta["description"] = self.meta["description"].replace(
            self.rights["changes_notice"], ""
        )
        with self.assertRaisesRegex(ValueError, "changes_notice"):
            require_content_rights_metadata(self.meta, self.preflight)

    def test_non_https_license_blocks(self):
        self.rights["license_url"] = "http://example.org/source-license"
        with self.assertRaisesRegex(ValueError, "must be HTTPS"):
            require_content_rights_metadata(self.meta, self.preflight)


if __name__ == "__main__":
    unittest.main()
