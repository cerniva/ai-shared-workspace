#!/usr/bin/env python3
"""Minimal AIL relay. Fake adapter only. No provider API.

Tests: A normal, B duplicate, C unsupported intent, D adapter failure.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "data" / "fixtures"
SEEN = FIX / "seen-cache.json"
LOG = FIX / "relay-run.log"

REQUIRED = ("from", "to", "intent", "id", "lang")
INTENTS = {
    "ask", "answer", "propose", "accept", "reject", "share",
    "ping", "pong", "meta", "task", "delegate", "analyze",
    "critique", "improve", "status", "review", "code",
    "summary", "learn", "evolve",
}


def parse_ail(text: str) -> dict:
    fields: dict = {}
    for line in str(text).strip().splitlines():
        m = re.match(r"^@([a-z]+):\s*(.*)$", line.strip(), re.I)
        if not m:
            break
        key = m.group(1).lower()
        if key in fields:
            return {"ok": False, "protocol_status": "invalid", "reason": "duplicate-header", "id": fields.get("id")}
        fields[key] = m.group(2).strip()
    missing = [k for k in REQUIRED if not fields.get(k)]
    if missing:
        return {"ok": False, "protocol_status": "invalid", "reason": "missing:" + ",".join(missing), "id": fields.get("id")}
    fields["ok"] = True
    fields["original_intent"] = fields["intent"]
    if fields["intent"].lower() not in INTENTS:
        fields["protocol_status"] = "unsupported"
    else:
        fields["protocol_status"] = "ok"
        fields["intent"] = fields["intent"].lower()
    return fields


def load_seen() -> dict:
    if not SEEN.exists():
        return {"ids": [], "executes": {}}
    return json.loads(SEEN.read_text())


def save_seen(state: dict) -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(state, indent=2) + "\n")


def log(line: str) -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(line + "\n")
    print(line)


def fake_adapter(msg: dict, fail: bool = False) -> dict:
    if fail:
        raise RuntimeError("adapter-down")
    pid = "msg-pong-auto-" + msg["id"]
    raw = (
        "@from: agent-a\n"
        "@to: system\n"
        "@intent: pong\n"
        f"@id: {pid}\n"
        f"@ref: {msg['id']}\n"
        "@lang: ail/1.1\n\n"
        "pong\n"
    )
    return parse_ail(raw)


def handle(raw: str, state: dict, fail_adapter: bool = False, max_attempts: int = 3) -> str:
    msg = parse_ail(raw)
    mid = msg.get("id") or "no-id"
    if not msg.get("ok"):
        log(f"INVALID {mid} {msg.get('reason')}")
        return "invalid"
    if mid in state["ids"]:
        log(f"DUP {mid} executes={state['executes'].get(mid, 0)}")
        return "duplicate"
    state["ids"].append(mid)
    if msg["protocol_status"] == "unsupported":
        log(f"UNSUPPORTED {mid} original_intent={msg['original_intent']}")
        save_seen(state)
        return "unsupported"
    if msg.get("to") != "agent-a":
        log(f"NO_ROUTE {mid} to={msg.get('to')}")
        save_seen(state)
        return "no-route"
    attempts = 0
    last_err = None
    while attempts < max_attempts:
        attempts += 1
        try:
            out = fake_adapter(msg, fail=fail_adapter)
            state["executes"][mid] = state["executes"].get(mid, 0) + 1
            if out.get("id") and out["id"] not in state["ids"]:
                state["ids"].append(out["id"])
            save_seen(state)
            log(f"OK {mid} attempt={attempts} -> {out.get('id')} executes={state['executes'][mid]}")
            return "ok"
        except Exception as e:
            last_err = str(e)
            log(f"FAIL {mid} attempt={attempts} err={last_err}")
    save_seen(state)
    log(f"DEAD_LETTER {mid} attempts={attempts}")
    return "dead-letter"


def run_tests() -> None:
    if LOG.exists():
        LOG.write_text("")
    state = {"ids": [], "executes": {}}
    save_seen(state)
    ping = "@from: system\n@to: agent-a\n@intent: ping\n@id: msg-ping-code-001\n@lang: ail/1.1\n\nping\n"
    a = handle(ping, state)
    b = handle(ping, state)
    bad = "@from: system\n@to: agent-a\n@intent: ACK\n@id: msg-bad-intent-001\n@lang: ail/1.1\n\nnope\n"
    c = handle(bad, state)
    fail_ping = "@from: system\n@to: agent-a\n@intent: ping\n@id: msg-fail-001\n@lang: ail/1.1\n\nping\n"
    d = handle(fail_ping, state, fail_adapter=True)
    log(f"TEST A={a} B={b} C={c} D={d}")
    log(f"executes ping={state['executes'].get('msg-ping-code-001', 0)} fail={state['executes'].get('msg-fail-001', 0)}")


if __name__ == "__main__":
    run_tests()
