"""research-learner handler for team-worker YAPAMADIM events (event type: team-research).

Input: repository_dispatch client_payload or workflow_dispatch inputs
{handoff_id, reason, task}. Asks the supervisor model chain (no key -> keyless
note, never silent) for a research finding on why the task failed and what is
needed, then appends it to the same handoff's notes in state/handoffs.json.
Writes nothing else; never dispatches workflows.
"""
from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.team_worker import HANDOFF_ID_RE, append_note, find_handoff, load_handoffs, redact

MARK = "research-learner (team-research)"


def read_payload(env: Mapping[str, str]) -> dict[str, str]:
    path = env.get("GITHUB_EVENT_PATH")
    event = json.loads(Path(path).read_text()) if path and Path(path).exists() else {}
    src = event.get("client_payload") or event.get("inputs") or {}
    return {k: str(src.get(k) or "") for k in ("handoff_id", "reason", "task")}


def research(payload: dict[str, str], *, adapter, handoffs: Path = Path("state/handoffs.json"),
             env: Mapping[str, str] | None = None, now: str | None = None) -> str:
    env = os.environ if env is None else env
    hid = payload.get("handoff_id", "")
    if not HANDOFF_ID_RE.match(hid):
        raise ValueError(f"invalid handoff_id: {hid!r}")
    item = find_handoff(load_handoffs(handoffs), hid)
    if item is None:
        raise ValueError(f"handoff {hid} not found")
    if any(MARK in str(n) for n in item.get("notes") or []):
        return "already_noted"
    if adapter is None:
        finding = "model anahtari yok; bulgu uretilemedi. Gereken: XAI/OPENAI/GEMINI/ANTHROPIC/DEEPSEEK anahtarlarindan biri."
    else:
        try:
            result: dict[str, Any] = adapter.run({
                "id": f"{hid}-research", "project": "ai-shared-workspace",
                "objective": f"team-worker bu gorevi yapamadi. Gorev: {payload.get('task')}. Neden: {payload.get('reason')}. "
                             "Kok nedeni ve cozum icin gereken adimlari arastir.",
                "evidence_requirements": ["kaynak URL veya repo yolu"]})
            finding = (str(result.get("recommendation") or "") + " | sonraki: " + str(result.get("next_action") or ""))[:800]
        except Exception as exc:
            finding = f"model cevap vermedi ({type(exc).__name__}: {exc})"
    now = now or datetime.now(timezone.utc).isoformat(timespec="seconds")
    append_note(handoffs, hid, redact(f"{MARK}: {finding}", env), now)
    return "noted"


def main() -> int:
    from scripts.backup_supervisor import supervisor_adapter
    out = research(read_payload(os.environ), adapter=supervisor_adapter())
    print(json.dumps({"team_research": out}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
