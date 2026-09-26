#!/usr/bin/env python3
"""Meta Model API desk worker. Reads messages/inbox-meta.md, writes from-meta.md."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(".")
INBOX = ROOT / "messages" / "inbox-meta.md"
OUT = ROOT / "messages" / "from-meta.md"
USER_ACTION = ROOT / "messages" / "user-action-required.md"

KEY = (os.environ.get("META_MODEL_API_KEY") or os.environ.get("MODEL_API_KEY") or "").strip()
MODEL = os.environ.get("META_MODEL", "muse-spark-1.3").strip()
ACTIVE = {"queued", "ready", "open", "run"}


def read(path: Path, limit: int | None = None) -> str:
    if not path.exists():
        return ""
    value = path.read_text(encoding="utf-8")
    return value if limit is None else value[:limit]


def field(text: str, name: str, default: str = "") -> str:
    m = re.search(rf"(?mi)^\s*{re.escape(name)}\s*:\s*(.*?)\s*$", text)
    return m.group(1).strip() if m else default


def append(path: Path, header: str, block: str) -> None:
    prev = read(path) or header
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prev.rstrip() + "\n" + block + "\n", encoding="utf-8")


TASK_MARKER = re.compile(r"(?m)^## TASK$")

def task_blocks(text: str) -> list[tuple[int, int, str]]:
    marks = list(TASK_MARKER.finditer(text))
    blocks = []
    for i, match in enumerate(marks):
        start = match.start()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        blocks.append((start, end, text[start:end]))
    return blocks


def select_active_task(text: str) -> str:
    for _, _, block in task_blocks(text):
        if field(block, "status", "idle").lower() in ACTIVE:
            return block
    return ""


def mark_task_status(text: str, task_id: str, status: str) -> str:
    for start, end, block in task_blocks(text):
        if field(block, "id") == task_id:
            lines = block.splitlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("status:"):
                    indent = line[:len(line) - len(line.lstrip())]
                    lines[i] = indent + f"status: {status}"
                    updated = chr(10).join(lines)
                    if block.endswith(chr(10)):
                        updated += chr(10)
                    return text[:start] + updated + text[end:]
            raise ValueError(f"status missing for Meta task {task_id}")
    raise ValueError(f"Meta task not found: {task_id}")

inbox = read(INBOX)
if not inbox:
    print("no inbox-meta.md")
    sys.exit(0)

task_text = select_active_task(inbox)
if not task_text:
    print("inbox içinde bekleyen Meta görevi yok; skip")
    sys.exit(0)

task_id = field(task_text, "id") or "meta-task"
project = field(task_text, "project", "workspace")
sender = field(task_text, "from", "team")
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
stamp = now.strftime("%Y%m%d-%H%M%S")
iso = now.isoformat(timespec="seconds")

if not KEY:
    block = f"""
---
id: MSG-{stamp}-meta-need-key
from: meta-worker
to: team
created_at: {iso}
project: {project}
status: blocked
---

intent: connection | blocked
evidence: META_MODEL_API_KEY / MODEL_API_KEY Actions secret yok.
decision: Consumer meta.ai sohbetine hat yok. İletişim yalnız Model API worker ile.
next-action: Furkan https://dev.meta.ai dashboard'dan key alıp repo Actions secret `META_MODEL_API_KEY` eklesin. Key'i sohbete yapıştırma.
blocker_if_any: secret missing
"""
    append(OUT, "# Meta AI çıkış kanalı\n", block)
    action = f"""
---
id: ACTION-{stamp}-meta-api-key
source: meta-worker
task: {task_id}
created_at: {iso}
status: open
---

## BAĞLANTI GEREKİYOR
- Servis / uygulama: Meta Model API (Muse Spark)
- Neden gerekli: Grok/ChatGPT ile Meta arasında otomatik masa hattı
- Hangi veriyi / yeteneği kazandırır: inbox-meta queued → from-meta yazma
- Bağlantı türü: GitHub Secret
- Kullanıcıdan gereken işlem: dev.meta.ai → API keys → Create; repo Settings → Secrets → Actions → `META_MODEL_API_KEY`
- Gerekli secret / izin adı: META_MODEL_API_KEY
- Kurulum adımları: key'i bir kez kopyala, secret'a koy, sohbete yazma; sonra inbox-meta status: queued
- Ücretsiz / ücretli: Meta Model API ücretli olabilir (dashboard)
- Öncelik: yüksek (iletişim hattı)
- Geçici alternatif: meta-ingest Action ile elle yapıştırma
"""
    append(USER_ACTION, "# User Action Required\n", action)
    INBOX.write_text(mark_task_status(inbox, task_id, "blocked"), encoding="utf-8")
    print("secret missing; task blocked and action written")
    sys.exit(0)

team = "\n\n".join(
    x
    for x in [
        read(ROOT / "docs" / "META_MANDATE.md", 2500),
        read(ROOT / "PROTOCOL.md", 4000),
        read(ROOT / "research" / "KNOWLEDGE_LEDGER.md", 2000),
    ]
    if x
)

prompt = f"""Sen ortak masa ekibinin Meta üyesisin (file-desk).
Türkçe yaz. Secret/ödeme/yayın/PayoutLens isteme.
Kısa, kanıtlı, tek next-action.

BAĞLAM:
{team}

GÖREV:
{task_text}
"""

payload = {"model": MODEL, "input": prompt}
req = urllib.request.Request(
    "https://api.meta.ai/v1/responses",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")[:1000]
    if exc.code == 429 or exc.code >= 500:
        print(f"Meta API HTTP {exc.code}; görev geçici hata nedeniyle kuyrukta tutuldu.", file=sys.stderr)
        sys.exit(1)
    note = f"Meta API HTTP {exc.code}: {body}"
    blocked = f"""
---
id: MSG-{stamp}-meta-blocked
from: meta-worker
to: team
in_reply_to: {task_id}
created_at: {iso}
project: {project}
status: blocked
---

intent: Meta API task blocked
evidence: {note}
decision: Bu görev otomatik tekrar denenmeyecek.
next-action: Meta API erişim/faturalandırma durumunu kontrol et; sonra yalnız bu görevi inbox-meta içinde tekrar queued yap.
blocker_if_any: HTTP {exc.code}
"""
    append(OUT, "# Meta AI çıkış kanalı\n", blocked)
    INBOX.write_text(mark_task_status(inbox, task_id, "blocked"), encoding="utf-8")
    print(f"Meta API HTTP {exc.code}; task {task_id} blocked without retry")
    sys.exit(0)
except Exception as exc:
    print(f"Meta API call failed: {exc}", file=sys.stderr)
    sys.exit(1)

reply = ""
if isinstance(raw, dict):
    if isinstance(raw.get("output_text"), str):
        reply = raw["output_text"]
    elif isinstance(raw.get("output"), list):
        bits = []
        for item in raw["output"]:
            if not isinstance(item, dict):
                continue
            for part in item.get("content") or []:
                if isinstance(part, dict) and part.get("type") in {"output_text", "text"}:
                    bits.append(part.get("text") or "")
        reply = "\n".join(bits)
    elif isinstance(raw.get("choices"), list) and raw["choices"]:
        msg = (raw["choices"][0] or {}).get("message") or {}
        reply = msg.get("content") or ""
reply = (reply or "").strip() or json.dumps(raw, ensure_ascii=False)[:4000]

msg_id = f"MSG-{stamp}-meta-api"
block = f"""
---
id: {msg_id}
from: meta-api
to: team
in_reply_to: {task_id}
created_at: {iso}
project: {project}
status: done
source_sender: {sender}
model: {MODEL}
---

{reply}
"""
append(OUT, "# Meta AI çıkış kanalı\n", block)
INBOX.write_text(mark_task_status(inbox, task_id, "done"), encoding="utf-8")
print(f"Meta yanıtı kaydedildi: {msg_id}; {len(reply)} karakter")
