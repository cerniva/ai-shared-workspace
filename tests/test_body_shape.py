import unittest

from scripts.worker_adapters import _body_shape


class BodyShapeTest(unittest.TestCase):
    def test_kinds_without_leaking_body(self):
        self.assertEqual(_body_shape("", "text/html"), "kind=empty len=0 content_type=text/html")
        self.assertIn("kind=html", _body_shape("<html>secret-ish</html>"))
        self.assertIn("kind=sse", _body_shape('data: {"x":1}\n\ndata: [DONE]', "text/event-stream"))
        self.assertIn("kind=truncated_or_multi_json", _body_shape('{"a":1}{"b":2}'))
        shape = _body_shape("hello secret token")
        self.assertIn("kind=text", shape)
        self.assertNotIn("secret", shape)


if __name__ == "__main__":
    unittest.main()
