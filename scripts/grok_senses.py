#!/usr/bin/env python3
"""Grok API reply worker for open ChatGPT → Grok file-desk messages."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
import re

from scripts.provider_config import make_adapter
from scripts.worker_adapters import MissingCredential, NonRetryableProviderError, RetryableProviderError

ROOT = Path(".")
INBOX = ROOT / "messages" / "chatgpt-to-grok.md"
OUT = ROOT / "messages" / "grok-to-chatgpt.md"
TEAM_MODEL = ROOT / "TEAM_OPERATING_MODEL.md"
PROTOCOL = ROOT / "PROTOCOL.md"
MODEL = "grok-4.7"
SPLIT = re.compile(r"(?m)^---[ \t]*$")


def parse_messages(text: str) -> list[dict[str, str]]:
    parts = SPLIT.split(text)
    messages: list[dict[str, str]] = []
    i = 1
    while i + 1 < len(parts):
        fields: dict[str, str] = {}
        for line in parts[i].strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                fields[key.strip()] = value.strip()
        if fields.get("id"):
            fields["body"] = parts[i + 1].strip()
            messages.append(fields)
        i += 2
    return messages


def unanswered_task() -> dict[str, str] | None:
    if not INBOX.exists():
        return None
    tasks = parse_messages(INBOX.read_text(encoding="utf-8"))
    replies = parse_messages(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    answered = {item.get("in_reply_to", "") for item in replies if item.get("in_reply_to")}
    for task in reversed(tasks):
        if (
            task.get("from") == "chatgpt"
            and task.get("to") == "grok"
            and task.get("status", "").lower() in {"open", "queued", "ready", "run"}
            and task.get("id") not in answered
        ):
            return task
    return None


def render_result(result: dict) -> str:
    lines = ["## Grok değerlendirmesi"]
    for key, title in [
        ("factual_findings", "Bulgular"),
        ("hypotheses", "Olasılıklar / varsayımlar"),
    ]:
        values = result.get(key) or []
        if values:
            lines.extend(["", f"### {title}"])
            lines.extend(f"- {value}" for value in values)
    evidence = result.get("evidence") or []
    if evidence:
        lines.extend(["", "### Kanıt"])
        for item in evidence:
            if isinstance(item, dict):
                desc = item.get("description") or item.get("status") or json.dumps(item, ensure_ascii=False)
                source = item.get("source")
                lines.append(f"- {desc}" + (f" — {source}" if source else ""))
            else:
                lines.append(f"- {item}")
    recommendation = result.get("recommendation")
    if recommendation:
        lines.extend(["", "### Öneri", str(recommendation)])
    next_action = result.get("next_action")
    if next_action:
        lines.extend(["", f"Sonraki adım: {next_action}"])
    confidence = result.get("confidence")
    if confidence is not None:
        lines.extend(["", f"Güven: {confidence}"])
    return "\n".join(lines)


def append_reply(task: dict[str, str], body: str, status: str = "done") -> str:
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
    stamp = now.strftime("%Y%m%d-%H%M%S")
    message_id = f"MSG-{stamp}-grok-api"
    block = f"""
---
id: {message_id}
from: grok-api
to: chatgpt
in_reply_to: {task.get('id', '')}
created_at: {now.isoformat(timespec='seconds')}
project: {task.get('project', 'workspace')}
status: {status}
---

{body}
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    previous = OUT.read_text(encoding="utf-8") if OUT.exists() else "# Grok → ChatGPT\n"
    OUT.write_text(previous.rstrip() + "\n" + block.strip() + "\n", encoding="utf-8")
    return message_id


def main() -> int:
    task = unanswered_task()
    if not task:
        print("Grok inbox idle: unanswered ChatGPT task yok.")
        return 0

    if not __import__("os").environ.get("XAI_API_KEY", "").strip():
        append_reply(
            task,
            "intent: grok-api | blocked\nevidence: XAI_API_KEY GitHub Actions secret tanımlı değil.\n"
            "decision: Bu görev otomatik tekrar denenmeyecek.\n"
            "next-action: Secret eklendikten sonra yeni bir ChatGPT→Grok görevi gönder.\n"
            "blocker_if_any: missing XAI_API_KEY",
            status="blocked",
        )
        print("XAI_API_KEY missing; task returned as blocked.")
        return 0

    team_context = "\n\n".join(
        path.read_text(encoding="utf-8")[:5000]
        for path in (TEAM_MODEL, PROTOCOL)
        if path.exists()
    )
    objective = (
        "Ekip modeli ve protokolü:\n" + team_context
        + "\n\nChatGPT'den gelen görev:\n" + task.get("body", "")
        + "\n\nTürkçe yanıt ver. Mantık, kanıt, risk ve uygulanabilir öneriyi ayır. "
        "Erişmediğin kaynağı görmüş gibi anlatma; yapmadığın işlemi yapılmış gösterme."
    )
    job = {
        "id": task.get("id", "grok-task"),
        "project": task.get("project", "workspace"),
        "objective": objective,
        "evidence_requirements": [
            "Do not invent repository or external evidence.",
            "State uncertainty and blockers explicitly.",
            "Give a concise, actionable answer in Turkish.",
        ],
    }
    try:
        result = make_adapter("grok").run(job)
    except RetryableProviderError as exc:
        print(f"Grok transient error; leave task unanswered for a later retry: {exc}", file=sys.stderr)
        return 1
    except (MissingCredential, NonRetryableProviderError) as exc:
        append_reply(
            task,
            f"intent: grok-api | blocked\nevidence: {type(exc).__name__}: {exc}\n"
            "decision: Bu görev otomatik tekrar denenmeyecek.\n"
            "next-action: XAI erişimini veya isteğin biçimini düzeltip yeni görev gönder.",
            status="blocked",
        )
        print(f"Grok task blocked: {exc}")
        return 0

    reply_id = append_reply(task, render_result(result))
    print(f"Grok yanıtı kaydedildi: {reply_id}; parent={task.get('id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
