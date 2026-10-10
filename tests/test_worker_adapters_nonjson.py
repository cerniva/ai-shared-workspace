import io
import unittest
from unittest import mock

from scripts import worker_adapters as wa


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class NonJsonBodyTest(unittest.TestCase):
    def test_empty_body_is_retryable_provider_error(self):
        with mock.patch.object(wa, "urlopen", return_value=_Resp(b"")):
            with self.assertRaises(wa.RetryableProviderError):
                wa._default_transport("https://x.invalid", {}, {}, 1.0)

    def test_html_body_is_retryable_provider_error(self):
        with mock.patch.object(wa, "urlopen", return_value=_Resp(b"<html>502</html>")):
            with self.assertRaises(wa.WorkerError):
                wa._default_transport("https://x.invalid", {}, {}, 1.0)

    def test_json_body_still_parsed(self):
        with mock.patch.object(wa, "urlopen", return_value=_Resp(b'{"ok": 1}')):
            self.assertEqual(wa._default_transport("https://x.invalid", {}, {}, 1.0), {"ok": 1})


if __name__ == "__main__":
    unittest.main()
