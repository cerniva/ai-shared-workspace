#!/usr/bin/env python3
"""Shared TinyFish web worker with durable run identity and idempotent execution."""
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
RUNS = ROOT / "state" / "tinyfish-runs.json"
FETCH_URL = "https://api.fetch.tinyfish.ai"
AGENT_RUN_URL = "https://agent.tinyfish.ai/v1/automation/run-async"
DEFAULT_FETCH_URL = "https://i19cci-4e.myshopify.com"
MAX_RESULT_CHARS = 4000
ALLOWED_HOSTS = {"i19cci-4e.myshopify.com", "docs.tinyfish.ai", "agent.tinyfish.ai", "example.com"}
TERMINAL = {"done", "failed", "blocked"}
PROHIBITED_GOAL_PATTERNS = (
    r"\b(buy|purchase|pay|checkout|satın al|ödeme)\b",
    r"\b(publish|post publicly|send publicly|yayınla)\b",
    r"\b(delete|remove account|sil)\b",
    r"\b(change|reset|değiştir).{0,20}\b(password|security|2fa|mfa|şifre|güvenlik)\b",
    r"\b(secret|password|api key|token|şifre|gizli anahtar)\b",
    r"\b(bypass|solve|atla|çöz).{0,20}\b(2fa|mfa|captcha|login|giriş)\b",
    r"\blog\s?in\b|\blogin\b|\bgiriş yap\b",
)

def now() -> str: return datetime.now(timezone.utc).isoformat()

def load_ledger(path: Path = RUNS) -> dict:
    if not path.exists(): return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8")); return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError): return {}

def save_ledger(ledger: dict, path: Path = RUNS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def task_record(ledger: dict, task_id: str) -> dict | None:
    value = ledger.get(task_id); return value if isinstance(value, dict) else None

def record_run_start(ledger: dict, task: dict[str, object], run_id: str) -> dict:
    task_id = str(task.get("id", "")); previous = task_record(ledger, task_id) or {}
    record = {"task_id": task_id, "requested_by": str(task.get("requested_by", "chatgpt")), "mode": str(task.get("mode", "fetch")), "status": "running", "run_id": run_id, "updated_at": now(), "last_error": "", "routed_event_keys": list(previous.get("routed_event_keys", []))}
    ledger[task_id] = record; return record

def record_terminal(ledger: dict, task_id: str, status: str, last_error: str = "") -> dict:
    record = dict(task_record(ledger, task_id) or {"task_id": task_id}); record.update({"status": status, "updated_at": now(), "last_error": last_error}); record.setdefault("requested_by", "chatgpt"); record.setdefault("mode", "fetch"); record.setdefault("run_id", ""); record.setdefault("routed_event_keys", []); ledger[task_id] = record; return record

def latest_task(text: str) -> str: return text.rsplit("## TASK", 1)[-1] if "## TASK" in text else text

def field(block: str, name: str) -> str:
    m = re.search(rf"(?im)^{re.escape(name)}:\s*(.+)$", block); return m.group(1).strip() if m else ""

def urls_from(block: str) -> list[str]:
    raw = field(block, "urls"); found = [u.strip() for u in re.split(r"[,\s]+", raw) if u.strip().startswith("http")]
    if not found: found = re.findall(r"https?://[^\s]+", block)
    clean = []
    for url in found[:10]:
        host = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0].lower()
        if host in ALLOWED_HOSTS or host.endswith(".myshopify.com"): clean.append(url.rstrip(")]."))
    return clean

def multiline_field(block: str, name: str) -> str:
    m = re.search(rf"(?im)^{re.escape(name)}:\s*\|\s*$", block)
    if not m: return field(block, name)
    lines = []
    for line in block[m.end():].splitlines():
        if not line.strip():
            if lines: lines.append("")
            continue
        if not re.match(r"^\s+", line): break
        lines.append(re.sub(r"^\s{1,2}", "", line))
    return "\n".join(lines).strip()

def parse_task(block: str) -> dict[str, object]:
    mode = (field(block, "mode") or "fetch").lower(); urls = urls_from(block)
    if mode == "fetch" and not urls: urls = [DEFAULT_FETCH_URL]
    return {"id": field(block, "id") or f"TF-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}", "requested_by": (field(block, "from") or "chatgpt").lower(), "mode": mode, "urls": urls, "url": field(block, "url"), "goal": multiline_field(block, "goal"), "status": (field(block, "status") or "").lower()}

def validate_task(task: dict[str, object]) -> tuple[bool, str]:
    mode = str(task.get("mode", "fetch"))
    if mode not in {"fetch", "browser"}: return False, f"unsupported mode: {mode}"
    if mode == "fetch" and not task.get("urls"): return False, "fetch requires at least one allowlisted URL"
    if mode == "browser" and (not task.get("url") or not task.get("goal")): return False, "browser requires url and goal"
    return True, ""

def browser_block_reason(task: dict[str, object]) -> str:
    goal = str(task.get("goal", "")).lower()
    for pattern in PROHIBITED_GOAL_PATTERNS:
        if re.search(pattern, goal, re.I): return "browser goal requires prohibited or authenticated action"
    return ""

def build_browser_payload(task: dict[str, object]) -> dict[str, object]:
    if task.get("mode") != "browser": raise ValueError("browser payload requires mode: browser")
    reason = browser_block_reason(task)
    if reason: raise ValueError(reason)
    return {"url": task["url"], "goal": task["goal"], "browser_profile": "lite", "agent_config": {"mode": "strict", "max_steps": 50, "max_duration_seconds": 300}}

def fetch(urls: list[str], key: str) -> dict[str, object]:
    req = urllib.request.Request(FETCH_URL, data=json.dumps({"urls": urls, "format": "markdown"}).encode(), method="POST", headers={"Content-Type": "application/json", "X-API-Key": key, "User-Agent": "cerniva-desk-tinyfish/3"})
    with urllib.request.urlopen(req, timeout=90) as resp: return json.loads(resp.read().decode())

def run_browser(task: dict[str, object], key: str) -> dict[str, object]:
    req = urllib.request.Request(AGENT_RUN_URL, data=json.dumps(build_browser_payload(task)).encode(), method="POST", headers={"Content-Type": "application/json", "X-API-Key": key, "User-Agent": "cerniva-desk-tinyfish/3"})
    with urllib.request.urlopen(req, timeout=60) as resp: return json.loads(resp.read().decode())

def append_result(task: dict[str, object], status: str, data: object) -> None:
    serialized = json.dumps(data, ensure_ascii=False, default=str)[:MAX_RESULT_CHARS]; block = f"\n---\nid: TF-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}\ntask_id: {task.get('id', '')}\nfrom: tinyfish\nrequested_by: {task.get('requested_by', 'chatgpt')}\nmode: {task.get('mode', 'fetch')}\nstatus: {status}\ncreated_at: {now()}\n---\n\n```json\n{serialized}\n```\n"; OUT.write_text((OUT.read_text(encoding="utf-8") if OUT.exists() else "# from-tinyfish\n") + block, encoding="utf-8")

def append_action_once(service: str, reason_code: str, reason: str) -> bool:
    text = ACTION.read_text(encoding="utf-8") if ACTION.exists() else ""
    for block in re.split(r"(?m)^---\s*$", text):
        if re.search(r"(?im)^status:\s*open\s*$", block) and re.search(rf"(?im)^service:\s*{re.escape(service)}\s*$", block) and re.search(rf"(?im)^reason_code:\s*{re.escape(reason_code)}\s*$", block): return False
    record = f"\n---\nid: ACTION-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-tinyfish\nsource: tinyfish-worker\nstatus: open\nservice: {service}\nreason_code: {reason_code}\ncreated_at: {now()}\n---\n\n## BAĞLANTI GEREKİYOR\n- Servis: {service}\n- Secret adı: TINYFISH_API_KEY\n- Neden: {reason}\n"; ACTION.write_text(text + record, encoding="utf-8"); return True

def mark_inbox(status: str, note: str) -> None:
    text = INBOX.read_text(encoding="utf-8") if INBOX.exists() else ""
    if "## TASK" in text:
        head, tail = text.rsplit("## TASK", 1); tail = re.sub(r"(?im)^status:\s*\S+", f"status: {status}", tail, count=1); INBOX.write_text(head + "## TASK" + tail + f"\nworker_note: {note}\n", encoding="utf-8")

def classify_http_status(code: int) -> tuple[str, str]:
    if code in (401, 403): return "api-permission", "TinyFish API key/permission rejected"
    if code == 402: return "credits-plan", "TinyFish Agent credits/plan required"
    if code == 429 or code >= 500: return "transient", f"TinyFish HTTP {code}; retryable later"
    return "http-error", f"TinyFish HTTP {code}"

def execute_task(task: dict[str, object], key: str, ledger: dict | None = None) -> tuple[str, object, str]:
    task_id = str(task.get("id", "")); existing = task_record(ledger, task_id) if ledger is not None else None
    if existing and existing.get("status") in TERMINAL: return str(existing["status"]), {"run_id": existing.get("run_id", ""), "reused": True}, str(existing.get("last_error", ""))
    if task.get("mode") == "browser" and existing and existing.get("status") in {"running", "retryable"} and existing.get("run_id"): return str(existing["status"]), {"run_id": existing["run_id"], "reused": True}, str(existing.get("last_error", ""))
    try:
        if task.get("mode") == "fetch":
            data = fetch(task["urls"], key)
            if ledger is not None: record_run_start(ledger, task, ""); record_terminal(ledger, task_id, "done", "")
            return "done", data, ""
        data = run_browser(task, key); run_id = str(data.get("run_id") or data.get("id") or "") if isinstance(data, dict) else ""
        if not run_id:
            reason = "TinyFish browser response missing run_id"
            if ledger is not None: record_run_start(ledger, task, ""); record_terminal(ledger, task_id, "blocked", reason)
            return "blocked", {"reason_code": "missing-run-id"}, reason
        if ledger is not None: record_run_start(ledger, task, run_id)
        return "running", {"run_id": run_id, "remote": data}, ""
    except urllib.error.HTTPError as exc:
        reason_code, reason = classify_http_status(exc.code); status = "retryable" if reason_code == "transient" else "blocked"
        if ledger is not None: record_run_start(ledger, task, str((existing or {}).get("run_id", ""))); record_terminal(ledger, task_id, status, reason)
        return status, {"http_status": exc.code, "reason_code": reason_code}, reason
    except Exception as exc:
        reason = str(exc)[:200]
        if ledger is not None: record_run_start(ledger, task, str((existing or {}).get("run_id", ""))); record_terminal(ledger, task_id, "blocked", reason)
        return "blocked", {"error": type(exc).__name__, "message": reason}, reason

def main() -> int:
    block = latest_task(INBOX.read_text(encoding="utf-8") if INBOX.exists() else ""); task = parse_task(block)
    if task.get("status") not in {"queued", "ready", "open", "run"}: return 0
    valid, reason = validate_task(task)
    if not valid: append_result(task, "failed", {"reason": reason}); mark_inbox("failed", reason); return 0
    safety_reason = browser_block_reason(task) if task.get("mode") == "browser" else ""
    if safety_reason: append_result(task, "failed", {"reason": safety_reason}); mark_inbox("failed", safety_reason); return 0
    key = os.environ.get("TINYFISH_API_KEY", "").strip()
    if not key: append_action_once("TinyFish", "missing-secret", "TINYFISH_API_KEY missing; worker skipped."); append_result(task, "blocked", {"reason_code": "missing-secret"}); mark_inbox("blocked", "missing TINYFISH_API_KEY"); return 0
    ledger = load_ledger(); status, data, reason = execute_task(task, key, ledger=ledger); save_ledger(ledger); append_result(task, status, data)
    if status == "done": mark_inbox("done", f"{task.get('mode')} ok"); return 0
    if status == "running": mark_inbox("running", "browser run persisted; awaiting reconciliation"); return 0
    if status == "retryable": mark_inbox("retryable", reason or "transient TinyFish error"); return 0
    reason_code = data.get("reason_code", "runtime-error") if isinstance(data, dict) else "runtime-error"
    if reason_code in {"api-permission", "credits-plan"}: append_action_once("TinyFish", str(reason_code), reason)
    mark_inbox("blocked", reason or str(reason_code)); return 0

if __name__ == "__main__": raise SystemExit(main())
