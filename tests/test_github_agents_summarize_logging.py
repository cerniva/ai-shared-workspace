"""_summarize must log why the model step failed instead of swallowing it silently."""
from __future__ import annotations

from scripts import github_agents
from scripts.worker_adapters import WorkerError


class _Failing:
    def run(self, _task):
        raise WorkerError("github_models HTTP 429 rate limit")


class _Empty:
    def run(self, _task):
        return {"recommendation": ""}


class _Ok:
    def run(self, _task):
        return {"recommendation": "Review the headline."}


def test_worker_error_is_logged(capsys):
    assert github_agents._summarize(_Failing(), "x") is None
    err = capsys.readouterr().err
    assert "model_unavailable" in err and "429" in err


def test_empty_recommendation_is_logged(capsys):
    assert github_agents._summarize(_Empty(), "x") is None
    assert "empty recommendation" in capsys.readouterr().err


def test_ok_returns_text(capsys):
    assert github_agents._summarize(_Ok(), "x") == "Review the headline."
    assert capsys.readouterr().err == ""
