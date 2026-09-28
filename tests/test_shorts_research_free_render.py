from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import shorts_research


BASE_SCORES = {key: 7 for key in shorts_research.CRITERIA}


def valid_packet() -> dict:
    """Return a legacy packet that satisfies the existing research gate."""
    return {
        "topic": "A surprising engineering fact",
        "why_selected": "Strong curiosity and visual potential",
        "trend_or_evergreen": "evergreen",
        "hook": "This tiny detail changes the whole machine.",
        "target_seconds": 20,
        "sources": ["https://example.com/a", "https://example.com/b"],
        "unique_angle": "Explain the hidden mechanism visually",
        "script_beats": ["hook", "mechanism", "payoff"],
        "visual_plan": ["close-up", "diagram", "result"],
        "audio_plan": "Narration with light background music",
        "title": "The tiny part that changes everything",
        "hashtags": ["engineering", "shorts"],
        "prepublish_checklist": {
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
        },
    }


class ShortsResearchFreeRenderTests(unittest.TestCase):
    """Pin backward-compatible scoring and conditional free-render requirements."""

    def test_legacy_candidate_without_optional_dimensions_keeps_neutral_score(self) -> None:
        """Missing new dimensions should contribute neutral values, not zeros or vetoes."""
        item = {
            "title": "legacy",
            "unique_angle": "new angle",
            "scores": dict(BASE_SCORES),
        }
        scored = shorts_research.score_item(item)
        self.assertEqual(scored["total"], sum(BASE_SCORES.values()) + 25.0)
        self.assertFalse(scored["veto"])
        self.assertEqual(scored["missing_criteria"], [])

    def test_equal_base_candidate_with_better_monetization_engagement_and_cost_ranks_higher(self) -> None:
        """Optional business/production signals should break otherwise equal base scores."""
        weak = {
            "title": "weak optional",
            "unique_angle": "angle one",
            "scores": {
                **BASE_SCORES,
                "monetization": 2,
                "engagement": 3,
                "low_production_cost": 2,
                "rights_safety": 5,
                "language_fit": 5,
            },
        }
        strong = {
            "title": "strong optional",
            "unique_angle": "angle two",
            "scores": {
                **BASE_SCORES,
                "monetization": 9,
                "engagement": 9,
                "low_production_cost": 9,
                "rights_safety": 5,
                "language_fit": 5,
            },
        }
        ranked = shorts_research.rank([weak, strong])
        self.assertEqual(ranked[0]["title"], "strong optional")
        self.assertGreater(ranked[0]["total"], ranked[1]["total"])

    def test_nan_reliability_uses_default_and_cannot_bypass_veto(self) -> None:
        """NaN is invalid input and must not turn into a passing reliability score."""
        item = {
            "title": "invalid reliability",
            "unique_angle": "still unique",
            "scores": {**BASE_SCORES, "reliability": float("nan")},
        }
        scored = shorts_research.score_item(item)
        self.assertTrue(scored["veto"])

    @patch("scripts.shorts_research.is_duplicate", return_value=False)
    def test_legacy_packet_does_not_require_free_render_fields(self, _duplicate) -> None:
        """Legacy packets must keep their existing gate contract."""
        blockers = shorts_research.gate_packet(valid_packet())
        for suffix in ("language", "content_type", "narration_text", "media_queries"):
            self.assertNotIn("missing_" + suffix, blockers)
        self.assertEqual(blockers, [])

    @patch("scripts.shorts_research.is_duplicate", return_value=False)
    def test_real_legacy_packet_remains_gate_compatible(self, _duplicate) -> None:
        """The repository's existing SHORT-RES-001 packet must not gain new blockers."""
        packet_path = shorts_research.SHORTS / "packets" / "SHORT-RES-001.json"
        packet = shorts_research.load_json(packet_path)
        self.assertFalse(packet.get("free_render_requested", False))
        self.assertEqual(shorts_research.gate_packet(packet), [])

    @patch("scripts.shorts_research.is_duplicate", return_value=False)
    def test_free_render_packet_requires_language_content_type_narration_and_queries(self, _duplicate) -> None:
        """Free rendering must fail before acquisition when packet inputs are incomplete."""
        packet = valid_packet()
        packet["free_render_requested"] = True
        blockers = shorts_research.gate_packet(packet)
        self.assertIn("missing_language", blockers)
        self.assertIn("missing_content_type", blockers)
        self.assertIn("missing_narration_text", blockers)
        self.assertIn("missing_media_queries", blockers)

        packet.update(
            {
                "language": "en",
                "content_type": "explainer",
                "narration_text": "A complete narration.",
                "media_queries": ["machine detail", "engineering mechanism"],
            }
        )
        self.assertEqual(shorts_research.gate_packet(packet), [])

    @patch("scripts.shorts_research.is_duplicate", return_value=False)
    def test_free_render_packet_accepts_turkish_or_english_language_string(self, _duplicate) -> None:
        """The gate should not hard-code one production language."""
        for language in ("tr", "tr-TR", "en", "en-US"):
            packet = valid_packet()
            packet.update(
                {
                    "free_render_requested": True,
                    "language": language,
                    "content_type": "explainer",
                    "narration_text": "Dil seçimine uygun özgün anlatım.",
                    "media_queries": ["visual one", "visual two"],
                }
            )
            with self.subTest(language=language):
                self.assertEqual(shorts_research.gate_packet(packet), [])


if __name__ == "__main__":
    unittest.main()
