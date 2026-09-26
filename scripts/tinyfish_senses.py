#!/usr/bin/env python3
"""TinyFish shared web worker: free Fetch by default, explicit guarded browser mode."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "messages" / "inbox-tinyfish.md"
OUT = ROOT / "messages" / "from-tinyfish.md"
ACTION = ROOT / "messages" / "user-action-required.md"
FETCH_URL = "https://api.fetch.tinyfish.ai"
AGENT_RUN_URL = "https://agent.tinyfish.ai/v1/automation/run"
ALLOWED_HOSTS = {"i19cci-4e.myshopify.com", "docs.tinyfish.ai", "agent.tinyfish.ai", "example.com"}
PROHIBITED_GOAL_PATTERNS = (
    r"\b(buy|purchase|pay|checkout)\b",
    r"\b(publish|post publicly|send publicly)\b",
    r"\b(delete|remove account)\b",
    r"\b(change|reset).{0,20}\b(password|security|2fa|mfa)\b",
    r"\b(secret|password|api key|token)\b",
    r"\b(bypass|solve).{0,20}\b(2fa|mfa|captcha|login)\b",
    r"\blog\s?in\b|\blogin\b",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def latest_task(text: str) -> str:
    return text.rsplit("## TASK", 1)[-1] if "## TASK" in text else text


def field(block: str, name: str) -> str:
    m = re.search(rf"(?im)^{re.escape(name)}:\s*(.+)$", block)
    return m.group(1).strip() if m else ""


def urls_from(block: str) -> list[str]:
    raw = field(block, "urls")
    found = [u.strip() for u in re.split(r"[,\s]+", raw) if u.strip().startswith("http")]
    if not found:
        found = re.findall(r"https?://[^\s]+", block)
    clean = []
    for url in found[:10]:
        host = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0].lower()
        if host in ALLOWED_HOSTS or host.endswith(".myshopify.com"):
            clean.append(url.rstrip(")]."))
    return clean


def multiline_field(block: str, name: str) -> str:
    m = re.search(rf"(?im)^{re.escape(name)}:\s*\|\s*$", block)
    if not m:
        return field(block, name)
    lines = []
    for line in block[m.end():].splitlines():
        if not line.strip():
            if lines:
                lines.append("")
            continue
        if not re.match(r"^\s+", line):
            break
        lines.append(re.sub(r"^\s{1,2}", "", line))
    return "\n".join(lines).strip()


def parse_task(block: str) -> dict[str, object]:
    return {
        "id": field(block, "id") or f"TF-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "requested_by": (field(block, "from") or "chatgpt").lower(),
        "mode": (field(block, "mode") or "fetch").lower(),
        "urls": urls_from(block),
        "url": field(block, "url"),
        "goal": multiline_field(block, "goal"),
        "status": (field(block, "status") or "").lower(),
    }


def validate_task(task: dict[str, object]) -> tuple[bool, str]:
    mode = str(task.get("mode", "fetch"))
    if mode not in {"fetch", "browser"}:
        return False, f"unsupported mode: {mode}"
    if mode == "fetch" and not task.get("urls"):
        return False, "fetch requires at least one allowlisted URL"
    if mode == "browser" and (not task.get("url") or not task.get("goal")):
        return False, "browser requires url and goal"
    return True, ""


def browser_block_reason(task: dict[str, object]) -> str:
    goal = str(task.get("goal", "")).lower()
    for pattern in PROHIBITED_GOAL_PATTERNS:
        if re.search(pattern, goal, re.I):
            return "browser goal requires prohibited or authenticated action"
    return ""


def build_browser_payload(task: dict[str, object]) -> dict[str, object]:
    if task.get("mode") != "browser":
        raise ValueError("browser payload requires mode: browser")
    reason = browser_block_reason(task)
    if reason:
        raise ValueError(reason)
    return {
        "url": task["url"],
        "goal": task["goal"],
        "browser_profile": "lite",
        "agent_config": {"mode": "strict", "max_steps": 50, "max_duration_seconds": 300},
    }


def run_browser(task: dict[str, object], key: str) -> dict[str, object]:
    payload = build_browser_payload(task)
    req = urllib.request.Request(
        AGENT_RUN_URL,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": key, "User-Agent": "cerniva-desk-tinyfish/2"},
    )
    with urllib.request.urlopen(req, timeout=330) as resp:
        return json.loads(resp.read().decode())


def append_action(reason: str) -> None:
    block = (
        f"\n---\nid: ACTION-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-tinyfish\n"
        f"source: tinyfish-worker\nstatus: open\ncreated_at: {now()}\n---\n\n"
        "## BAĞLANTI GEREKİYOR\n- Servis: TinyFish Fetch API\n- Secret adı: TINYFISH_API_KEY\n"
        "- Nereye: GitHub → cerniva/ai-shared-workspace → Settings → Secrets → Actions\n"
        "- Anahtar: agent.tinyfish.ai/api-keys (sohbete yapıştırma)\n"
        f"- Neden: {reason}\n- ChatGPT plugin OAuth şart değil; masa worker yeterli.\n"
    )
    ACTION.write_text(ACTION.read_text(encoding="utf-8") + block if ACTION.exists() else block, encoding="utf-8")


def mark_inbox(status: str, note: str) -> None:
    text = INBOX.read_text(encoding="utf-8") if INBOX.exists() else ""
    if "## TASK" in text:
        head, tail = text.rsplit("## TASK", 1)
        tail = re.sub(r"(?im)^status:\s*\S+", f"status: {status}", tail, count=1)
        INBOX.write_text(head + "## TASK" + tail + f"\nworker_note: {note}\n", encoding="utf-8")


def fetch(urls: list[str], key: str) -> dict:
    body = json.dumps({"urls": urls, "format": "markdown"}).encode()
    req = urllib.request.Request(FETCH_URL, data=body, method="POST", headers={"Content-Type": "application/json", "X-API-Key": key, "User-Agent": "cerniva-desk-tinyfish/1"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    text = INBOX.read_text(encoding="utf-8") if INBOX.exists() else ""
    block = latest_task(text)
    if not re.search(r"(?im)^status:\s*(queued|ready|open|run)\s*$", block):
        return 0
    key = os.environ.get("TINYFISH_API_KEY", "").strip()
    if not key:
        append_action("TINYFISH_API_KEY missing; fetch skipped.")
        mark_inbox("blocked", "missing TINYFISH_API_KEY")
        return 0
    urls = urls_from(block) or ["https://i19cci-4e.myshopify.com"]
    try:
        data = fetch(urls, key)
        snippet = json.dumps(data, ensure_ascii=False)[:4000]
        OUT.write_text((OUT.read_text(encoding="utf-8") if OUT.exists() else "# from-tinyfish\n") + f"\n---\nid: TF-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}\ncreated_at: {now()}\nurls: {', '.join(urls)}\nstatus: done\n---\n\n```json\n{snippet}\n```\n", encoding="utf-8")
        mark_inbox("done", "fetch ok")
    except urllib.error.HTTPError as exc:
        mark_inbox("blocked", f"HTTP {exc.code}")
        append_action(f"TinyFish HTTP {exc.code}")
    except Exception as exc:
        mark_inbox("blocked", type(exc).__name__)
        append_action(str(exc)[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
