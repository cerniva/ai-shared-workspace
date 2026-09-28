import unittest

from scripts.shorts_research import CRITERIA, gate_packet, rank, score_item


CRITICAL_CHECKS = {
    "facts_verified": True,
    "sources_reliable": True,
    "strong_first_2s": True,
    "no_empty_intro": True,
    "audio_planned": True,
    "portrait_9_16_planned": True,
    "not_previously_published": True,
    "title_matches": True,
    "rights_ok": True,
    "publishable_quality_planned": True,
}


def valid_packet():
    return {
        "topic": "Compatibility topic qz9265",
        "why_selected": "test fixture",
        "trend_or_evergreen": "evergreen",
        "hook": "QZ9265 surprising compatibility hook",
        "target_seconds": 20,
        "sources": ["https://example.com/source-a", "https://example.com/source-b"],
        "unique_angle": "fixture-specific angle",
        "script_beats": ["beat one", "beat two"],
        "visual_plan": ["visual one"],
        "audio_plan": "narration",
        "title": "QZ9265 compatibility title",
        "hashtags": ["#test"],
        "prepublish_checklist": dict(CRITICAL_CHECKS),
    }


class ShortsResearchFreeRenderTests(unittest.TestCase):
    def test_legacy_candidate_without_optional_dimensions_keeps_neutral_score(self):
        scores = {key: 8 for key in CRITERIA}
        item = {"id": "legacy", "unique_angle": "yes", "scores": scores}
        scored = score_item(item)
        self.assertEqual(scored["total"], len(CRITERIA) * 8 + 25)
        self.assertFalse(scored["veto"])

    def test_equal_base_candidate_with_better_monetization_engagement_and_cost_ranks_higher(self):
        base = {key: 8 for key in CRITERIA}
        low = {
            "id": "low",
            "unique_angle": "yes",
            "scores": {
                **base,
                "monetization": 2,
                "engagement": 2,
                "low_production_cost": 2,
                "rights_safety": 2,
                "language_fit": 2,
            },
        }
        high = {
            "id": "high",
            "unique_angle": "yes",
            "scores": {
                **base,
                "monetization": 9,
                "engagement": 9,
                "low_production_cost": 9,
                "rights_safety": 9,
                "language_fit": 9,
            },
        }
        self.assertEqual(rank([low, high])[0]["id"], "high")

    def test_legacy_packet_does_not_require_free_render_fields(self):
        blockers = gate_packet(valid_packet())
        self.assertNotIn("missing_language", blockers)
        self.assertNotIn("missing_content_type", blockers)
        self.assertNotIn("missing_narration_text", blockers)
        self.assertNotIn("missing_media_queries", blockers)
        self.assertEqual(blockers, [])

    def test_free_render_packet_requires_language_content_type_narration_and_queries(self):
        packet = valid_packet()
        packet["free_render_requested"] = True
        blockers = gate_packet(packet)
        self.assertIn("missing_language", blockers)
        self.assertIn("missing_content_type", blockers)
        self.assertIn("missing_narration_text", blockers)
        self.assertIn("missing_media_queries", blockers)

        packet.update({
            "language": "tr",
            "content_type": "short_fact",
            "narration_text": "Kısa ve özgün bir anlatım.",
            "media_queries": ["  ", ""],
        })
        self.assertIn("missing_media_queries", gate_packet(packet))

    def test_free_render_packet_accepts_turkish_or_english_language_string(self):
        for language, narration in (("tr", "Türkçe anlatım"), ("en", "English narration")):
            with self.subTest(language=language):
                packet = valid_packet()
                packet.update({
                    "free_render_requested": True,
                    "language": language,
                    "content_type": "short_fact",
                    "narration_text": narration,
                    "media_queries": ["vertical science footage"],
                })
                self.assertEqual(gate_packet(packet), [])


if __name__ == "__main__":
    unittest.main()
