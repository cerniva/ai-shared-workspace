#!/usr/bin/env python3
"""Read queued Gemini requests, call Gemini API, write responses."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(".")
REQ_DIR = ROOT / "requests" / "gemini"
RES_DIR = ROOT / "responses" / "gemini"
YT_DIR = ROOT / "research" / "youtube"
KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
YT_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?v=[\w-]+|youtu\.be/[\w-]+)")


def now_tr() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))


def parse_front(text: str) -> tuple[dict, str]:
    meta: dict = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2].strip()
    return meta, body


def call_gemini(prompt: str, urls: list[str]) -> str:
    if not KEY:
        return "ERROR: GEMINI_API_KEY secret yok. Repo → Settings → Secrets → Actions."
    parts = [{
        "text": (
            "Sen ekibin duyu organısın. Video varsa izle veya caption kullan. "
            "Uydurma transcript yazma. Türkçe yanıt ver. "
            "Başlık, kanal, zaman damgalı özet, iddialar, uygulanabilir fikirler, belirsizlik.\n\n"
            + prompt
        )
    }]
    for u in urls[:3]:
        parts.append({"file_data": {"file_uri": u}})
    payload = json.dumps({"contents": [{"role": "user", "parts": parts}]}).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        raw = urllib.request.urlopen(req, timeout=180).read()
    except Exception as e:
        return f"ERROR: Gemini API {e}"
    data = json.loads(raw.decode())
    cands = data.get("candidates") or []
    if not cands:
        return "ERROR: boş yanıt " + json.dumps(data)[:2000]
    bits = [p.get("text", "") for p in ((cands[0].get("content") or {}).get("parts") or [])]
    return "\n".join(b for b in bits if b).strip() or json.dumps(data)[:2000]


def main() -> None:
    REQ_DIR.mkdir(parents=True, exist_ok=True)
    RES_DIR.mkdir(parents=True, exist_ok=True)
    YT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in REQ_DIR.glob("REQ-*.md"))
    if not files:
        print("no REQ-*.md")
        return
    handled = 0
    for path in files:
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_front(raw)
        if meta.get("status", "queued").lower() not in {"queued", "open", ""}:
            continue
        urls = YT_RE.findall(raw)
        if meta.get("url"):
            urls = [meta["url"]] + urls
        seen = []
        for u in urls:
            if u not in seen:
                seen.append(u)
        reply = call_gemini((body or raw)[:12000], seen)
        ts = now_tr().strftime("%Y%m%d-%H%M%S")
        rid = meta.get("id") or path.stem
        out = RES_DIR / f"RES-{path.stem}.md"
        out.write_text(
            f"---\nid: RES-{ts}\nin_reply_to: {rid}\nfrom: gemini-api\n"
            f"project: {meta.get('project', 'workspace')}\nstatus: done\n---\n\n{reply}\n",
            encoding="utf-8",
        )
        if seen:
            (YT_DIR / f"{path.stem}.md").write_text(
                f"# YouTube notes {rid}\n\nurls: {', '.join(seen)}\n\n{reply[:4000]}\n",
                encoding="utf-8",
            )
        meta["status"] = "done"
        head = "---\n" + "\n".join(f"{k}: {v}" for k, v in meta.items()) + "\n---\n\n"
        path.write_text(head + body + "\n", encoding="utf-8")
        handled += 1
        print("handled", path.name)
    if handled == 0:
        print("no queued requests")


if __name__ == "__main__":
    main()
