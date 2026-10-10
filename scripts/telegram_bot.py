#!/usr/bin/env python3
"""Free Telegram chat bot for the shared workspace, run by GitHub Actions polling.

Independent of Grok Bot. Polls getUpdates (offset in state/telegram_offset.json),
answers only TELEGRAM_ALLOWED_CHAT_ID. Never performs publish/payment actions:
workflow dispatch is restricted to an explicit check/test/render allowlist.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OFFSET_PATH = ROOT / "state" / "telegram_offset.json"
HANDOFFS_PATH = ROOT / "state" / "handoffs.json"
CHATGPT_READ = ROOT / "messages" / "chatgpt-to-read.md"
AGENTS_REPORT = ROOT / "messages" / "agents-report-latest.md"
MAX_CTX = 6000
MAX_REPLY = 3900

# command -> (agent / handoff actor, workflow file, output paths or globs)
AGENTS: dict[str, dict[str, Any]] = {
    "yedek": {"agent": "backup-supervisor", "workflow": "backup-supervisor.yml",
              "outputs": ["messages/backup-supervisor-latest.md", "intake/chatgpt/backup-supervisor-*.patch"]},
    "yurutucu": {"agent": "automation-runner", "workflow": "automation-runner.yml",
                 "outputs": ["state/automation_runner.json"]},
    "arastirma": {"agent": "research-learner", "workflow": "research-learner.yml",
                  "outputs": ["state/research_learner.json", "intake/promotions/*research-learner*.json"]},
    "rapor": {"agent": "agents-reporter", "workflow": "agents-reporter.yml",
              "outputs": ["messages/agents-report-latest.md", "state/agents_history.json"]},
}

# Only check/test/render workflows may be dispatched. automation-runner is NOT
# here: it holds actions:write and can chain other workflows.
DISPATCH_ALLOWLIST = frozenset({
    "backup-supervisor.yml", "research-learner.yml", "agents-reporter.yml",
    "worker-orchestration-tests.yml", "web-worker-tests.yml", "shorts-render-tests.yml",
    "ai-roster-check.yml", "handoff-audit.yml", "plan-learnings-check.yml", "shorts-free-render.yml",
})
FORBIDDEN_RE = re.compile(r"upload|publish|yayin|yayın|payment|odeme|ödeme|pay|shopify|meta-bridge|deploy|release",
                          re.IGNORECASE)

SYSTEM_RULES = (
    "Sen Furkan'ın paylaşılan AI çalışma alanı için Telegram asistanısın. Her zaman Türkçe, kısa ve net cevap ver. "
    "Yayın (publish/upload), ödeme veya para harcayan hiçbir işlem yapamazsın ve yapmış gibi davranma; "
    "böyle bir istek gelirse bunun Furkan'ın manuel onayını gerektirdiğini söyle. Yalnızca verilen bağlama dayan."
)

Http = Callable[[str, dict[str, Any] | None], dict[str, Any]]


def is_dispatch_allowed(workflow: str) -> bool:
    return workflow in DISPATCH_ALLOWLIST and not FORBIDDEN_RE.search(workflow)


def default_http(url: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode() or "{}"
    return json.loads(body)


def _read(path: Path, limit: int = MAX_CTX) -> str:
    try:
        return path.read_text(encoding="utf-8")[-limit:]
    except OSError:
        return ""


def load_offset(path: Path = OFFSET_PATH) -> int:
    try:
        return int(json.loads(path.read_text(encoding="utf-8")).get("offset", 0))
    except (OSError, ValueError, AttributeError):
        return 0


def save_offset(offset: int, path: Path = OFFSET_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"offset": offset}, indent=2) + "\n", encoding="utf-8")


def open_handoffs(path: Path = HANDOFFS_PATH) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [i for i in data.get("items", []) if i.get("status") in ("open", "claimed")]


def handoff_summary(path: Path = HANDOFFS_PATH) -> str:
    items = open_handoffs(path)
    if not items:
        return "Açık handoff yok."
    return "\n".join(f"- {i['id']} [{i['status']}] {i['from']}→{i['to']}: {i['task'][:120]}" for i in items[:15])


def agent_output(cmd: str, root: Path = ROOT) -> str:
    parts = []
    for pattern in AGENTS[cmd]["outputs"]:
        for p in sorted(root.glob(pattern))[-2:]:
            parts.append(f"### {p.relative_to(root)}\n{_read(p, 2500)}")
    return "\n\n".join(parts) or "(bu ajan için henüz çıktı yok)"


def ask_llm(question: str, context: str, *, env=None, adapter_factory=None) -> str:
    """Use provider failover (Gemini first). Returns Turkish text or a safe fallback."""
    try:
        if adapter_factory is None:
            from scripts.provider_config import make_failover_adapter as adapter_factory
        adapter = adapter_factory(env=env if env is not None else os.environ)
        job = {
            "id": "telegram-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "project": "telegram-bot",
            "objective": f"{SYSTEM_RULES}\n\nBağlam:\n{context[:MAX_CTX]}\n\nSoru: {question}\n"
                         "Cevabını 'recommendation' alanına Türkçe yaz.",
            "evidence_requirements": [],
        }
        result = adapter.run(job)
        text = str(result.get("recommendation") or "").strip()
        return text or "Model boş cevap döndü."
    except Exception as exc:  # noqa: BLE001 - bot must never crash on provider errors
        return f"Şu an yapay zeka sağlayıcısına ulaşılamadı ({type(exc).__name__}). Lütfen sonra tekrar dene."


def add_handoff(task: str, *, receiver: str, runner=subprocess.run, file: Path = HANDOFFS_PATH) -> str:
    item_id = "TG-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    cmd = [sys.executable, str(ROOT / "scripts" / "handoff.py"), "--file", str(file), "add",
           "--id", item_id, "--from", "furkan", "--to", receiver, "--task", task[:500],
           "--reason", "Furkan Telegram üzerinden görev verdi", "--evidence", "telegram-bot"]
    proc = runner(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return f"Handoff eklenemedi: {(proc.stdout or proc.stderr or '').strip()[:200]}"
    return f"Görev eklendi: {item_id} (furkan→{receiver})"


TEAM_WORK_EVENT = "team-work"


def dispatch_team_work(message_key: str, *, env=None, http=None) -> str:
    """repository_dispatch team-work {source: telegram, message_key, handoff_id} after /gorev.
    Commits made with GITHUB_TOKEN start no push workflows; repository_dispatch does.
    comms_watch never re-dispatches TG-* handoffs, so one message is processed once."""
    values = os.environ if env is None else env
    token, repo = values.get("GITHUB_TOKEN", ""), values.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        return "team-work tetiklenmedi: GITHUB_TOKEN/GITHUB_REPOSITORY yok."
    http = http or default_http
    try:
        http(f"https://api.github.com/repos/{repo}/dispatches",
             {"event_type": TEAM_WORK_EVENT,
              "client_payload": {"source": "telegram", "message_key": message_key, "handoff_id": message_key}},
             {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
    except Exception as exc:  # noqa: BLE001
        return f"team-work tetiklenemedi: {type(exc).__name__}"
    return f"team-work tetiklendi: {message_key}"


def gorev(task: str, *, env=None, runner=subprocess.run, http=None) -> str:
    out = add_handoff(task, receiver="chatgpt", runner=runner)
    m = re.match(r"Görev eklendi: (TG-[0-9-]+)", out)
    if not m:
        return out
    return out + "\n" + dispatch_team_work(m.group(1), env=env, http=http)


def dispatch_workflow(workflow: str, *, env=None, http=None) -> str:
    if not is_dispatch_allowed(workflow):
        return f"'{workflow}' tetiklenemez: yalnızca check/test/render workflow'ları izinli; yayın/ödeme asla."
    values = os.environ if env is None else env
    token, repo = values.get("GITHUB_TOKEN", ""), values.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        return "Workflow tetikleme için GITHUB_TOKEN/GITHUB_REPOSITORY yok."
    http = http or default_http
    try:
        http(f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches", {"ref": "main"},
             {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
    except Exception as exc:  # noqa: BLE001
        return f"Tetikleme başarısız: {type(exc).__name__}"
    return f"{workflow} tetiklendi."


def knowledge_answer(question: str, *, limit: int = 5, query=None) -> str:
    """/bilgi: search the knowledge ledger + source catalog (read-only, no LLM)."""
    if query is None:
        from scripts.knowledge_query import query_knowledge as query
    from scripts.knowledge_query import format_hits
    try:
        hits = query(question, limit=limit)
    except Exception as exc:  # noqa: BLE001
        return f"Bilgi araması başarısız: {type(exc).__name__}"
    return format_hits(hits)[:MAX_REPLY]


def handle_text(text: str, *, env=None, adapter_factory=None, runner=subprocess.run, http=None) -> str:
    text = (text or "").strip()
    if not text:
        return "Boş mesaj."
    head, _, rest = text.partition(" ")
    cmd = head.split("@")[0].lstrip("/").lower() if head.startswith("/") else ""
    rest = rest.strip()
    if cmd in ("start", "yardim", "help"):
        return ("Komutlar: /durum, /bilgi <soru>, /gorev <metin>, /yedek, /yurutucu, /arastirma, /rapor "
                "(arkasına metin → o ajana görev; 'calistir' → izinliyse tetikle), /tetikle <workflow.yml>. "
                "Serbest metin → yapay zeka cevabı.")
    if cmd == "durum":
        ctx = f"chatgpt-to-read.md:\n{_read(CHATGPT_READ, 3000)}\n\nAçık handoff'lar:\n{handoff_summary()}"
        return ask_llm("Çalışma alanının güncel durumunu kısaca özetle.", ctx, env=env, adapter_factory=adapter_factory) \
            + "\n\nAçık handoff'lar:\n" + handoff_summary()
    if cmd == "gorev":
        return gorev(rest, env=env, runner=runner, http=http) if rest else "Kullanım: /gorev <metin>"
    if cmd == "bilgi":
        return knowledge_answer(rest) if rest else "Kullanım: /bilgi <soru>"
    if cmd == "tetikle":
        return dispatch_workflow(rest, env=env, http=http) if rest else "Kullanım: /tetikle <workflow.yml>"
    if cmd in AGENTS:
        spec = AGENTS[cmd]
        if rest.lower() in ("calistir", "çalıştır", "tetikle"):
            return dispatch_workflow(spec["workflow"], env=env, http=http)
        if rest:
            return add_handoff(rest, receiver=spec["agent"], runner=runner)
        return ask_llm(f"{spec['agent']} ajanının son çıktısını özetle; önemli bulguları ve sonraki adımı söyle.",
                       agent_output(cmd), env=env, adapter_factory=adapter_factory)
    if cmd:
        return "Bilinmeyen komut. /yardim yaz."
    ctx = f"Açık handoff'lar:\n{handoff_summary()}\n\nAjan raporu:\n{_read(AGENTS_REPORT, 3000)}"
    return ask_llm(text, ctx, env=env, adapter_factory=adapter_factory)


def run_once(*, env=None, http: Callable[..., dict[str, Any]] | None = None, adapter_factory=None,
             runner=subprocess.run, offset_path: Path = OFFSET_PATH) -> int:
    values = os.environ if env is None else env
    token = values.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("::notice::TELEGRAM_BOT_TOKEN missing; telegram bot skipped")
        return 0
    http = http or default_http
    api = f"https://api.telegram.org/bot{token}"
    allowed = {c.strip() for c in values.get("TELEGRAM_ALLOWED_CHAT_ID", "").split(",") if c.strip()}
    offset = load_offset(offset_path)
    try:
        updates = http(f"{api}/getUpdates", {"offset": offset, "timeout": 0}).get("result", [])
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::getUpdates failed: {type(exc).__name__}")
        return 0
    announced: set[str] = set()
    handled = 0
    for upd in updates:
        offset = max(offset, int(upd.get("update_id", 0)) + 1)
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat_id = str((msg.get("chat") or {}).get("id", ""))
        if not chat_id:
            continue
        if not allowed:
            if chat_id not in announced:
                announced.add(chat_id)
                _send(http, api, chat_id, f"Chat id: {chat_id}\nBunu GitHub'da TELEGRAM_ALLOWED_CHAT_ID olarak ekle.")
            continue
        if chat_id not in allowed:
            continue
        reply = handle_text(msg.get("text", ""), env=values, adapter_factory=adapter_factory, runner=runner)
        _send(http, api, chat_id, reply)
        handled += 1
    save_offset(offset, offset_path)
    print(f"telegram bot: {len(updates)} updates, {handled} handled")
    return 0


def _send(http, api: str, chat_id: str, text: str) -> None:
    try:
        http(f"{api}/sendMessage", {"chat_id": chat_id, "text": text[:MAX_REPLY]})
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::sendMessage failed: {type(exc).__name__}")


if __name__ == "__main__":
    raise SystemExit(run_once())
