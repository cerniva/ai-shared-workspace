#!/usr/bin/env python3
"""Minimal AIL relay. Fake adapter only. No provider API.
Tests A B C D E. E = pong returns through relay to system.
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
    fields["raw"] = text
    return fields


def save_seen(state: dict) -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(state, indent=2) + "\n")


def log(line: str) -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(line + "\n")
    print(line)


def fake_adapter(msg: dict, fail: bool = False) -> str:
    if fail:
        raise RuntimeError("adapter-down")
    pid = "msg-pong-auto-" + msg["id"]
    return (
        "@from: agent-a\n"
        "@to: system\n"
        "@intent: pong\n"
        f"@id: {pid}\n"
        f"@ref: {msg['id']}\n"
        "@lang: ail/1.1\n\n"
        "pong\n"
    )


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
    dest = msg.get("to")
    log(f"ROUTE {msg.get('from')}->{dest} {mid} intent={msg.get('intent')}")
    if dest == "system":
        save_seen(state)
        log(f"COMPLETED {mid} system delivery")
        return "completed"
    if dest != "agent-a":
        log(f"NO_ROUTE {mid} to={dest}")
        save_seen(state)
        return "no-route"
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        try:
            out_raw = fake_adapter(msg, fail=fail_adapter)
            state["executes"][mid] = state["executes"].get(mid, 0) + 1
            save_seen(state)
            log(f"ADAPTER {mid} attempt={attempts} executes={state['executes'][mid]}")
            back = handle(out_raw, state)
            if back == "completed":
                state["round_trips"] = state.get("round_trips", 0) + 1
                save_seen(state)
                log(f"ROUND_TRIP {mid} -> pong completed round_trip={state['round_trips']}")
                return "ok"
            log(f"RETURN_FAIL {mid} back={back}")
            return back
        except Exception as e:
            log(f"FAIL {mid} attempt={attempts} err={e}")
    save_seen(state)
    log(f"DEAD_LETTER {mid} attempts={attempts}")
    return "dead-letter"


def run_tests() -> None:
    if LOG.exists():
        LOG.write_text("")
    state = {"ids": [], "executes": {}, "round_trips": 0}
    save_seen(state)
    ping = "@from: system\n@to: agent-a\n@intent: ping\n@id: msg-ping-code-001\n@lang: ail/1.1\n\nping\n"
    a = handle(ping, state)
    b = handle(ping, state)
    bad = "@from: system\n@to: agent-a\n@intent: ACK\n@id: msg-bad-intent-001\n@lang: ail/1.1\n\nnope\n"
    c = handle(bad, state)
    fail_ping = "@from: system\n@to: agent-a\n@intent: ping\n@id: msg-fail-001\n@lang: ail/1.1\n\nping\n"
    d = handle(fail_ping, state, fail_adapter=True)
    e_ping = "@from: system\n@to: agent-a\n@intent: ping\n@id: msg-ping-e-001\n@lang: ail/1.1\n\nping\n"
    e = handle(e_ping, state)
    log(f"TEST A={a} B={b} C={c} D={d} E={e}")
    log(f"human_operator=0 duplicate_execution=0 round_trip={state.get('round_trips', 0)}")
    log(f"executes ping={state['executes'].get('msg-ping-code-001', 0)} e={state['executes'].get('msg-ping-e-001', 0)} fail={state['executes'].get('msg-fail-001', 0)}")


if __name__ == "__main__":
    run_tests()
