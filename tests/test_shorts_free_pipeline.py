import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

try:
    from scripts import shorts_free_pipeline as pipeline
except ImportError:
    pipeline = None

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "shorts_free_pipeline.py"

CRITICAL_CHECKS = {
    "facts_verified": True, "sources_reliable": True, "strong_first_2s": True,
    "no_empty_intro": True, "audio_planned": True, "portrait_9_16_planned": True,
    "not_previously_published": True, "title_matches": True, "rights_ok": True,
    "publishable_quality_planned": True,
}

def valid_packet(language="en", narration="A short original narration for the pipeline."):
    return {"topic":"Pipeline fixture topic zx7314","why_selected":"test fixture","trend_or_evergreen":"evergreen","hook":"ZX7314 pipeline hook","target_seconds":18,"sources":["https://example.com/a","https://example.com/b"],"unique_angle":"pipeline fixture angle","script_beats":["one","two"],"visual_plan":["stock visual"],"audio_plan":"narration","title":"ZX7314 pipeline title","hashtags":["#test"],"prepublish_checklist":dict(CRITICAL_CHECKS),"free_render_requested":True,"language":language,"content_type":"short_fact","narration_text":narration,"media_queries":["vertical forest","vertical river"]}

def asset(provider, asset_id, media_type="video", suffix="mp4"):
    return {"provider":provider,"provider_asset_id":asset_id,"source_url":f"https://example.com/source/{asset_id}","download_url":f"https://example.com/media/{asset_id}.{suffix}","media_type":media_type,"license_note":"test license","creator":"fixture creator","retrieved_at":"2026-09-28T00:00:00Z"}

def fake_download(item, destination):
    destination=Path(destination); destination.parent.mkdir(parents=True,exist_ok=True); destination.write_bytes(b"fixture"); return destination

class ShortsFreePipelineTests(unittest.TestCase):
    def setUp(self): self.assertIsNotNone(pipeline,"scripts.shorts_free_pipeline must exist")
    def _write_packet(self,base,packet):
        path=base/"packet.json"; path.write_text(json.dumps(packet,ensure_ascii=False),encoding="utf-8"); return path
    def _prepare(self, base, packet=None, search_results=None):
        if packet is None: packet=valid_packet()
        if search_results is None: search_results=[asset("pexels","1")]
        with patch.object(pipeline,"search_free_media",return_value=search_results), patch.object(pipeline,"download_asset",side_effect=fake_download), patch.object(pipeline,"_probe_real_video",return_value=None):
            return pipeline.prepare_render_bundle(self._write_packet(base,packet),base/"work",env={})
    def test_pipeline_refuses_packet_that_fails_research_gate(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); packet=valid_packet(); packet["prepublish_checklist"]["rights_ok"]=False
            with patch.object(pipeline,"search_free_media") as search:
                with self.assertRaisesRegex(ValueError,"research gate"): pipeline.prepare_render_bundle(self._write_packet(base,packet),base/"work",env={})
            search.assert_not_called()
    def test_pipeline_uses_media_queries_in_order_and_deduplicates_assets(self):
        first=[asset("pexels","same"),asset("pexels","unique-a")]; second=[asset("pexels","same"),asset("pixabay","unique-b")]
        with tempfile.TemporaryDirectory() as td, patch.object(pipeline,"search_free_media",side_effect=[first,second]) as search, patch.object(pipeline,"download_asset",side_effect=fake_download), patch.object(pipeline,"_probe_real_video",return_value=None):
            base=Path(td); result=pipeline.prepare_render_bundle(self._write_packet(base,valid_packet()),base/"work",env={})
            search.assert_has_calls([call("vertical forest",env={},limit=6),call("vertical river",env={},limit=6)])
            self.assertEqual(len(result["assets"]),3)
            provenance=json.loads(Path(result["provenance"]).read_text(encoding="utf-8")); self.assertEqual([(i["provider"],i["provider_asset_id"]) for i in provenance],[("pexels","same"),("pixabay","unique-b"),("pexels","unique-a")])
    def test_pipeline_reserves_a_visual_slot_for_each_query_before_filling_extras(self):
        first=[asset("pexels","forest-1"),asset("pexels","forest-2"),asset("pexels","forest-3")]; second=[asset("pexels","river-1")]
        with tempfile.TemporaryDirectory() as td, patch.object(pipeline,"search_free_media",side_effect=[first,second]), patch.object(pipeline,"download_asset",side_effect=fake_download), patch.object(pipeline,"_probe_real_video",return_value=None):
            base=Path(td); result=pipeline.prepare_render_bundle(self._write_packet(base,valid_packet()),base/"work",env={}); ids=[i["provider_asset_id"] for i in json.loads(Path(result["provenance"]).read_text())]; self.assertEqual(ids[:2],["forest-1","river-1"]); self.assertEqual(len(ids),3)
    def test_pipeline_writes_provenance_without_secrets(self):
        secret_env={"PEXELS_API_KEY":"pexels-secret-value-123","PIXABAY_API_KEY":"pixabay-secret-value-456"}
        with tempfile.TemporaryDirectory() as td, patch.object(pipeline,"search_free_media",return_value=[asset("pexels","1")]), patch.object(pipeline,"download_asset",side_effect=fake_download), patch.object(pipeline,"_probe_real_video",return_value=None):
            base=Path(td); result=pipeline.prepare_render_bundle(self._write_packet(base,valid_packet()),base/"work",env=secret_env); text=Path(result["provenance"]).read_text(); self.assertNotIn(secret_env["PEXELS_API_KEY"],text); self.assertNotIn(secret_env["PIXABAY_API_KEY"],text)
    def test_content_probe_rejects_fake_mp4_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fake.mp4"; path.write_bytes(b"not a video")
            with self.assertRaisesRegex(RuntimeError,"not recognized as video content"): pipeline._probe_real_video(path)
    def test_turkish_packet_defaults_to_tr_voice(self): self.assertEqual(pipeline.default_espeak_voice("tr-TR"),"tr")
    def test_english_packet_defaults_to_en_us_voice(self): self.assertEqual(pipeline.default_espeak_voice("en-GB"),"en-us")
    def test_unknown_language_requires_explicit_narration_voice(self):
        with self.assertRaisesRegex(ValueError,"narration_voice"): pipeline.default_espeak_voice("de")
        self.assertEqual(pipeline.default_espeak_voice("de","de"),"de")
    def test_build_srt_uses_mobile_readable_chunks_and_packet_language_text(self):
        text="Türkiye için kısa altyazı metni mobil ekranda rahat okunmalı ve anlam korunmalı."; srt=pipeline.build_srt(text,12,max_chars=24); lines=[x for x in srt.splitlines() if x and " --> " not in x and not x.isdigit()]; self.assertTrue(all(len(x)<=24 for x in lines)); self.assertEqual(" ".join(lines),text)
    def test_render_manifest_contains_local_paths_only(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); result=self._prepare(base,search_results=[asset("pixabay","2")]); manifest=json.loads(Path(result["render_manifest"]).read_text()); self.assertEqual(manifest["production_gates"]["content_probe"],"ffprobe"); self.assertTrue(manifest["visuals"])
    def test_direct_cli_help_runs_without_repo_import_error(self):
        result=subprocess.run([sys.executable,str(SCRIPT),"--help"],cwd=ROOT,capture_output=True,text=True,timeout=30); self.assertEqual(result.returncode,0,result.stderr or result.stdout)

if __name__=="__main__": unittest.main()
