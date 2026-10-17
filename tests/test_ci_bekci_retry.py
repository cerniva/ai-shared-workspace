"""ci_bekci GitHub client retries transient 5xx on GET (run 39005222509 died on a 502)."""
import io
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ci_bekci  # noqa: E402


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _err(code):
    return urllib.error.HTTPError("https://api.github.com/x", code, "err", {}, None)


def test_get_retries_502_then_succeeds(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=30):
        calls.append(req)
        if len(calls) < 3:
            raise _err(502)
        return _Resp(b"[]")

    monkeypatch.setattr(ci_bekci.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr("time.sleep", lambda s: None)
    gh = ci_bekci.GitHub("o/r", "t")
    assert gh.request("GET", "/issues") == []
    assert len(calls) == 3


def test_get_does_not_retry_404(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=30):
        calls.append(req)
        raise _err(404)

    monkeypatch.setattr(ci_bekci.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr("time.sleep", lambda s: None)
    gh = ci_bekci.GitHub("o/r", "t")
    try:
        gh.request("GET", "/issues")
    except urllib.error.HTTPError as e:
        assert e.code == 404
    else:
        raise AssertionError("expected HTTPError")
    assert len(calls) == 1


def test_post_is_not_retried(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=30):
        calls.append(req)
        raise _err(502)

    monkeypatch.setattr(ci_bekci.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr("time.sleep", lambda s: None)
    gh = ci_bekci.GitHub("o/r", "t")
    try:
        gh.request("POST", "/issues", {"title": "x"})
    except urllib.error.HTTPError:
        pass
    assert len(calls) == 1
