#!/usr/bin/env python3
"""Minimal AIL relay. No new headers. No fake provider calls.

Usage:
  python3 relay/minimal_relay.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEN = ROOT / "data" / "fixtures" / "seen-cache.json"
LOG = ROOT / "data" / "fixtures" / "relay-run.log"

INTENTS = {
    "ail/1.1": {
        "ask", "answer", "propose", "accept", "reject", "share",
        "ping", "pong", "meta", "task", "delegate", "analyze",
        "critique", "improve", "status", "review", "code",
        "summary", "learn", "evolve",
    }
}


def parse_ail(text: str) -> dict:
    fields = {}
    for line in text.strip().splitlines():
        m = re.match(r"^@([a-z]+):\s*(.*)$", line.strip(), re.I)
        if not m:
            break
        key = m.group(1).lower()
        if key in fields:
            return {"valid": False, "reason": "duplicate-header", "id": fields.get("id")}
        fields[key] = m.group(2).strip()
    required = ("from", "to", "intent", "id", "lang")
    if not all(fields.get(k) for k in required):
        return {"valid": False, "reason": "missing-field", "id": fields.get("id")}
    intent = fields["intent"].lower()
    lang = fields["lang"].lower()
    if intent not in INTENTS.get(lang, set()):
        fields["intent_raw"] = fields["intent"]
        fields["intent"] = "unknown"
    fields["valid"] = True
    fields["intent"] = fields["intent"].lower()
    return fields


def load_seen() -> set:
    if not SEEN.exists():
        return set()
    return set(json.loads(SEEN.read_text()).get("ids", []))


def save_seen(ids: set) -> None:
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps({"ids": sorted(ids)}, indent=2) + "\n")


def log(line: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(line + "\n")
    print(line)


def fake_a(msg: dict) -> str:
    return (
        "@from: agent-a\n"
        "@to: system\n"
        "@intent: pong\n"
        f"@id: msg-pong-auto-{msg['id']}\n"
        f"@ref: {msg['id']}\n"
        "@lang: ail/1.1\n\n"
        "pong\n"
    )


def handle(raw: str, seen: set) -> str:
    msg = parse_ail(raw)
    mid = msg.get("id")
    if not msg.get("valid"):
        log(f"DROP {mid} {msg.get('reason')}")
        return "FATAL_DROPPED"
    if mid in seen:
        log(f"DUP {mid} skip")
        return "DUPLICATE"
    seen.add(mid)
    save_seen(seen)
    if msg["to"] == "agent-a" and msg["intent"] == "ping":
        out = fake_a(msg)
        out_msg = parse_ail(out)
        if out_msg.get("valid") and out_msg["id"] not in seen:
            seen.add(out_msg["id"])
            save_seen(seen)
        log(f"OK {mid} -> {out_msg.get('id')}")
        return out
    log(f"NO_ADAPTER {mid} to={msg['to']}")
    return "NO_ADAPTER"


def main() -> None:
    seen = load_seen()
    ping = (
        "@from: system\n"
        "@to: agent-a\n"
        "@intent: ping\n"
        "@id: msg-ping-code-001\n"
        "@lang: ail/1.1\n\n"
        "ping\n"
    )
    first = handle(ping, seen)
    second = handle(ping, seen)
    log(f"RESULT first={first.splitlines()[0] if first.startswith('@') else first}")
    log(f"RESULT second={second}")


if __name__ == "__main__":
    main()
