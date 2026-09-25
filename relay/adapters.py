"""Provider adapters. Same relay core. No key => no call.

This ChatGPT/Grok chat session is NOT these adapters.
"""
from __future__ import annotations

import os


class NoKey(RuntimeError):
    pass


def openai_api_adapter(_msg: dict) -> dict:
    if not os.environ.get("OPENAI_API_KEY"):
        raise NoKey("OPENAI_API_KEY missing")
    raise NoKey("live OpenAI call not enabled in this freeze")


def grok_api_adapter(_msg: dict) -> dict:
    if not os.environ.get("XAI_API_KEY"):
        raise NoKey("XAI_API_KEY missing")
    raise NoKey("live xAI call not enabled in this freeze")
