#!/usr/bin/env python3
import json, os, re, sys, urllib.request, datetime
from pathlib import Path

ROOT = Path(".")
INBOX = ROOT / "messages" / "inbox-gemini.md"
OUT = ROOT / "messages" / "gemini-to-chatgpt.md"
KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL = "gemini-2.5-flash"

if not KEY:
    sys.exit("GEMINI_API_KEY secret yok. Repo Settings → Secrets → Actions.")

text = INBOX.read_text(encoding="utf-8")
if re.search(r"status:\s*idle", text, re.I):
    print("inbox idle; skip")
    sys.exit(0)

urls = re.findall(r"https?://(?:www\.)?(?:youtube\.com/watch\?v=[\w-]+|youtu\.be/[\w-]+)", text)
prompt = text[-8000:]
parts = [{
    "text": (
        "Sen ekibin duyu organısın (Gemini API). YouTube/video varsa izle veya caption kullan. "
        "Uydurma transcript yazma. Çıktı: başlık, kanal, zaman damgalı özet, iddialar, uygulanabilir fikirler, belirsizlik. "
        "Türkçe yaz.\n\nGÖREV:\n" + prompt
    )
}]
for u in urls[:3]:
    parts.append({"file_data": {"file_uri": u}})

body = json.dumps({"contents": [{"role": "user", "parts": parts}]}).encode()
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    raw = urllib.request.urlopen(req, timeout=180).read()
except Exception as e:
    reply = f"Gemini API hata: {e}"
else:
    data = json.loads(raw.decode())
    cands = data.get("candidates") or []
    if not cands:
        reply = "Gemini boş döndü: " + json.dumps(data)[:1500]
    else:
        bits = []
        for p in ((cands[0].get("content") or {}).get("parts") or []):
            if "text" in p:
                bits.append(p["text"])
        reply = "\n".join(bits).strip() or json.dumps(data)[:1500]

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime("%Y%m%d-%H%M%S")
block = (
    f"\n\n---\nid: MSG-{now}-gemini-api\nfrom: gemini-api\nto: chatgpt\n"
    f"in_reply_to: inbox-gemini\ncreated_at: {now}\nproject: workspace\nstatus: done\n---\n\n{reply}\n"
)
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    prev = OUT.read_text(encoding="utf-8")
else:
    prev = "# Gemini API → ChatGPT / Grok\n"
OUT.write_text(prev.rstrip() + block, encoding="utf-8")

# prevent retrigger loop
INBOX.write_text(
    "# Inbox → Gemini API\n\n## TASK\nstatus: idle\nfrom: system\nproject: workspace\nurl:\nprompt: |\n  Bekleme.\n",
    encoding="utf-8",
)
print("wrote gemini reply", len(reply))
