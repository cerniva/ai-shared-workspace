#!/usr/bin/env python3
"""Check Grok/ChatGPT desk health and recommend the safe write path."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G2C = ROOT / "messages" / "grok-to-chatgpt.md"
C2G = ROOT / "messages" / "chatgpt-to-grok.md"
STATE = ROOT / "state" / "now.json"

def main() -> None:
    problems = []
    for p in (G2C, C2G, STATE):
        if not p.exists():
            problems.append(f"missing:{p.relative_to(ROOT)}")
    state = {}
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"invalid-state:{exc}")
    agents = state.get("agents", {})
    bot_ready = all(k in agents for k in ("grok_bot", "github_takipci", "gorev_yurutucu"))
    result = {
        "healthy": not problems,
        "problems": problems,
        "preferred_grok_write_path": "grok-bot -> desk_bridge -> grok-to-chatgpt",
        "fallback_when_grok_connector_broken": "ChatGPT writes only explicit Grok handoff delta; Grok reads last 2",
        "bot_execution_layer_ready": bot_ready,
        "source_of_truth": "state/now.json",
        "protected_projects": state.get("protected_projects", ["payoutlens"]),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
