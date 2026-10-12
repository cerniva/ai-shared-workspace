import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Import the function under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from youtube_upload import load_metadata, require_explicit_declarations


class MetadataBoolParseTests(unittest.TestCase):
    def _write(self, obj):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(obj, f)
        f.close()
        return Path(f.name)

    def test_string_false_is_false_not_true(self):
        path = self._write({
            "title": "t",
            "description": "d",
            "selfDeclaredMadeForKids": "false",
            "containsSyntheticMedia": "false",
        })
        try:
            meta = load_metadata(path)
            self.assertIs(meta["selfDeclaredMadeForKids"], False)
            self.assertIs(meta["containsSyntheticMedia"], False)
        finally:
            path.unlink(missing_ok=True)

    def test_string_true_is_true(self):
        path = self._write({
            "title": "t",
            "description": "d",
            "selfDeclaredMadeForKids": "true",
            "containsSyntheticMedia": "TRUE",
        })
        try:
            meta = load_metadata(path)
            self.assertIs(meta["selfDeclaredMadeForKids"], True)
            self.assertIs(meta["containsSyntheticMedia"], True)
        finally:
            path.unlink(missing_ok=True)

    def test_real_bools_pass_through(self):
        path = self._write({
            "title": "t",
            "description": "d",
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        })
        try:
            meta = load_metadata(path)
            self.assertIs(meta["selfDeclaredMadeForKids"], False)
            self.assertIs(meta["containsSyntheticMedia"], True)
        finally:
            path.unlink(missing_ok=True)

    def test_invalid_string_raises(self):
        path = self._write({
            "title": "t",
            "description": "d",
            "selfDeclaredMadeForKids": "yes",
        })
        try:
            with self.assertRaises(ValueError):
                load_metadata(path)
        finally:
            path.unlink(missing_ok=True)

    def test_absent_keys_use_defaults_later(self):
        path = self._write({"title": "t", "description": "d"})
        try:
            meta = load_metadata(path)
            self.assertNotIn("selfDeclaredMadeForKids", meta)
            self.assertNotIn("containsSyntheticMedia", meta)
        finally:
            path.unlink(missing_ok=True)


class ExplicitDeclarationGateTests(unittest.TestCase):
    def test_missing_declarations_fail_closed(self):
        with self.assertRaises(ValueError) as ctx:
            require_explicit_declarations({"title": "t", "description": "d"})
        self.assertIn("selfDeclaredMadeForKids", str(ctx.exception))
        self.assertIn("containsSyntheticMedia", str(ctx.exception))

    def test_one_missing_declaration_fails(self):
        with self.assertRaises(ValueError):
            require_explicit_declarations({"title": "t", "description": "d", "selfDeclaredMadeForKids": False})

    def test_explicit_declarations_pass(self):
        require_explicit_declarations({"title": "t", "description": "d",
                                       "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True})


if __name__ == "__main__":
    unittest.main()
