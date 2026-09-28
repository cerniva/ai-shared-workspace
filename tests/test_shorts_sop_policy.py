import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOP = ROOT / "research" / "youtube" / "SHORTS_SOP.md"
MODULE = ROOT / "knowledge" / "shorts" / "RESEARCH_MODULE.md"


class ShortsSopPolicyTests(unittest.TestCase):
    def test_sop_is_dynamic_and_free_first(self):
        text = SOP.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertNotIn("Mutfak hattı öncelikli", text)
        self.assertNotIn("Üretim: HeyGen grafik / ElevenLabs", text)
        self.assertIn("free-first", lower)
        self.assertIn("Pexels", text)
        self.assertIn("Pixabay", text)
        self.assertIn("FFmpeg", text)
        self.assertIn("konu, format ve dil", lower)
        self.assertIn("gelir", lower)
        self.assertIn("etkileşim", lower)
        self.assertIn("retention", lower)
        self.assertIn("telif", lower)
        self.assertIn("maliyet", lower)

    def test_research_module_preserves_gates_and_makes_paid_render_fallback(self):
        text = MODULE.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertIn("scripts/shorts_preflight.py", text)
        self.assertIn("scripts/youtube_upload.py", text)
        self.assertIn("gate", lower)
        self.assertIn("preflight", lower)
        self.assertIn("review", lower)
        self.assertIn("yayın", lower)
        self.assertIn("free-first", lower)
        self.assertIn("Pexels", text)
        self.assertIn("Pixabay", text)
        self.assertIn("FFmpeg", text)
        self.assertIn("fallback", lower)
        self.assertIn("kredi harcayan", lower)


if __name__ == "__main__":
    unittest.main()
