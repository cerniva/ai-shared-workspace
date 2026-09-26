#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from connectors.youtube_client import compact_video_bundle, YouTubeDataError
except Exception:
    compact_video_bundle = None
    YouTubeDataError = RuntimeError

ROOT = Path(".")
INBOX = ROOT / "messages" / "inbox-gemini.md"
OUT = ROOT / "messages" / "gemini-to-chatgpt.md"
USER_ACTION = ROOT / "messages" / "user-action-required.md"
YT_DIR = ROOT / "research" / "youtube"

KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()
ACTIVE_STATUSES = {"queued", "ready", "open", "run"}

def read(path: Path, limit: int | None = None) -> str:
    if not path.exists():
        return ""
    value = path.read_text(encoding="utf-8")
    return value if limit is None else value[:limit]

def field(text: str, name: str, default: str = "") -> str:
    m = re.search(rf"(?mi)^\s*{re.escape(name)}\s*:\s*(.*?)\s*$", text)
    return m.group(1).strip() if m else default

def extract_youtube_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>\]]+", text)
    clean = []
    for u in urls:
        u = u.rstrip(".,;")
        if ("youtube.com/" in u or "youtu.be/" in u) and u not in clean:
            clean.append(u)
    return clean[:10]

if not INBOX.exists():
    sys.exit("messages/inbox-gemini.md bulunamadı.")

inbox = read(INBOX)
status = field(inbox, "status", "idle").lower()
if status not in ACTIVE_STATUSES:
    print(f"inbox status={status!r}; çalıştırılmadı")
    sys.exit(0)

# Defence in depth: never put private connector analysis into a public response.
if os.environ.get("REPO_PRIVATE", "false").lower() != "true" and any(
    field(inbox, name).lower() in {"true", "1", "yes", "on", "evet"}
    for name in ("use_shopify", "use_youtube_analytics")
):
    sys.exit("Private connector task blocked in public workspace.")

if not KEY:
    sys.exit("GEMINI_API_KEY secret eksik.")

task_id = field(inbox, "id") or "gemini-task"
project = field(inbox, "project", "workspace")
sender = field(inbox, "from", "chatgpt")
youtube_urls = extract_youtube_urls(inbox)

youtube_data_context = ""
if youtube_urls:
    if compact_video_bundle is None:
        youtube_data_context = "YouTube Data connector yüklenemedi."
    elif not os.environ.get("YOUTUBE_API_KEY", "").strip():
        youtube_data_context = (
            "YOUTUBE_DATA_API_STATUS: not_connected\n"
            "YOUTUBE_API_KEY GitHub Secret henüz yok. "
            "Video doğrudan Gemini ile analiz edilebilir; ancak yapılandırılmış metadata, "
            "kanal istatistikleri, arama ve yorum verisi için bağlantı gerekir."
        )
    else:
        bundles = []
        for u in youtube_urls[:3]:
            try:
                bundles.append(compact_video_bundle(u))
            except Exception as exc:
                bundles.append({"url": u, "error": str(exc)})
        youtube_data_context = (
            "YOUTUBE_DATA_API_STATUS: connected\n"
            + json.dumps(bundles, ensure_ascii=False)[:14000]
        )

team_context = "\n\n".join(
    x for x in [
        read(ROOT / "TEAM_OPERATING_MODEL.md", 10000),
        read(ROOT / "PROTOCOL.md", 10000),
        read(ROOT / "research" / "SOURCES.md", 6000),
        read(ROOT / "research" / "KNOWLEDGE_LEDGER.md", 8000),
        read(ROOT / "reports" / "LATEST.md", 12000),
        read(ROOT / "docs" / "TASK_ROUTING.md", 6000),
        read(ROOT / "tasks" / "agent_capacity.json", 4000),
    ] if x
)

instruction = f"""Sen ortak AI ekibinin Gemini API üyesisin.

Sen yalnızca YouTube/video işçisi değilsin. Finans, yazılım, Shopify, ürün geliştirme, içerik, araştırma, fikir üretme, eleştiri, planlama ve problem çözme dahil uygun olan her konuda ChatGPT ve Grok'a destek verirsin. Video/YouTube sadece özel güçlü yönlerinden biridir.

ORTAK BAĞLAM:
{team_context}

GÖREV:
{inbox}

YOUTUBE DATA API BAĞLAMI:
{youtube_data_context}

GENEL ÇIKTI KURALLARI:
- Türkçe yaz.
- Görevi doğrudan çözmeye çalış.
- Gerekli olduğunda kaynak/kanıt, varsayım, risk ve belirsizlikleri ayır.
- Emin olmadığın şeyi kesin gerçek gibi yazma.
- ChatGPT/Grok'un sonraki adımda kullanabileceği somut öneri veya çıktı üret.
- Kullanıcının aktif projelerine uygulanabilir noktaları özellikle belirt.
- Finans konusunda tahmin, görüş ve doğrulanmış olguyu ayır.
- Kod/yazılım görevinde mümkün olduğunca uygulanabilir teknik çözüm ver.
- Yaratıcı görevde birden fazla güçlü alternatif üretmekten çekinme.
- Eleştiri görevi verilirse zayıf noktaları açıkça belirt.
- Bir görevi mevcut erişimlerinle tamamlayamıyorsan sessiz kalma ve genel cevapla geçiştirme.
- Önce verilen bağlamda mevcut bağlantının durumunu kontrol et. Kısa süreli API hatası, kota, kod hatası veya isteğe bağlı ek veri için kullanıcıdan yeni anahtar ya da kurulum isteme; mevcut işle sürdürülebilen sonucu ver ve teknik hatayı ekibe bildir.
- Yalnızca bu görev için gerçekten vazgeçilmez, mevcut araçlarla karşılanamayan bir insan girişi/izin/secret gerektiğinde şu bölümü ekle:

## BAĞLANTI GEREKİYOR
- Servis / uygulama:
- Neden gerekli:
- Hangi veriyi / yeteneği kazandırır:
- Bağlantı türü: API | OAuth | MCP | Plugin | GitHub Secret | diğer
- Kullanıcıdan gereken işlem:
- Gerekli secret / izin adı:
- Kurulum adımları:
- Ücretsiz / ücretli:
- Öncelik:
- Bağlantı kurulmadan yapılabilecek geçici alternatif:

- Eğer hiçbir bağlantı gerekmiyor ama başka bir teknik engel varsa "## BLOKE" başlığıyla nedenini ve çözümünü yaz.
- Eksik erişim yüzünden başarısız olduğunda mümkünse doğrudan hangi connector dosyasının veya workflow değişikliğinin gerektiğini de belirt.

MEDYA/VIDEO VARSA EK KURALLAR:
- Erişim biçimini belirt: video analizi, caption/transcript veya erişilemedi.
- Mümkünse zaman damgaları kullan.
- Uydurma transcript üretme.
- Üçüncü taraf içeriğin uzun tam transcriptini üretme; sadık özet ve gerekli kısa alıntıları kullan.
"""

parts = [{"text": instruction}]
for url in youtube_urls:
    parts.append({"file_data": {"file_uri": url}})

payload = {
    "contents": [{"role": "user", "parts": parts}],
    "generationConfig": {"temperature": 0.2}
}

req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json", "x-goog-api-key": KEY},
    method="POST",
)

data = None
reply = None
last_error = None

for attempt, delay in enumerate([0, 5, 15, 30], start=1):
    if delay:
        time.sleep(delay)
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            raw = response.read().decode("utf-8")
        data = json.loads(raw)
        last_error = None
        break
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:4000]
        last_error = f"Gemini API HTTP {exc.code} hatası:\n\n{body}"
        # A daily quota is not fixed by four rapid calls; retry on a later run.
        if exc.code == 429 and "GenerateRequestsPerDayPerProjectPerModel" in body:
            break
        if exc.code not in (429, 500, 502, 503, 504):
            break
        print(f"geçici Gemini hatası {exc.code}; deneme {attempt}/4")
    except Exception as exc:
        last_error = f"Gemini API çağrısı başarısız: {type(exc).__name__}: {exc}"
        print(f"Gemini çağrı hatası; deneme {attempt}/4")

if data is None:
    # Keep queued tasks intact so scheduled runs can retry without human intervention.
    # An API error must not be recorded as completed work.
    print(last_error or "Gemini API başarısız oldu.", file=sys.stderr)
    sys.exit(1)
else:
    candidates = data.get("candidates") or []
    bits = []
    if candidates:
        for part in ((candidates[0].get("content") or {}).get("parts") or []):
            if isinstance(part, dict) and part.get("text"):
                bits.append(part["text"])
    reply = "\n".join(bits).strip()
    if not reply:
        print("Gemini anlamlı metin döndürmedi; görev kuyrukta bırakıldı.", file=sys.stderr)
        sys.exit(1)

now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
stamp = now.strftime("%Y%m%d-%H%M%S")
iso = now.isoformat(timespec="seconds")
msg_id = f"MSG-{stamp}-gemini-api"

block = f"""

---
id: {msg_id}
from: gemini-api
to: chatgpt
in_reply_to: {task_id}
created_at: {iso}
project: {project}
status: done
source_sender: {sender}
model: {MODEL}
youtube_urls: {json.dumps(youtube_urls, ensure_ascii=False)}
---

{reply}
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
previous = read(OUT) or "# Gemini API → ChatGPT / Grok\n"
OUT.write_text(previous.rstrip() + block + "\n", encoding="utf-8")

needs_user = ("## BAĞLANTI GEREKİYOR" in reply) or ("## BLOKE" in reply)
if needs_user:
    action_prev = read(USER_ACTION)
    if not action_prev:
        action_prev = "# User Action Required\n\nGemini veya ekip bir insan işlemi gerektiğinde buraya kayıt bırakır.\n"
    action_block = f"""

---
id: ACTION-{stamp}-{task_id}
source: gemini-api
task: {task_id}
created_at: {iso}
status: open
---

{reply}
"""
    USER_ACTION.parent.mkdir(parents=True, exist_ok=True)
    USER_ACTION.write_text(action_prev.rstrip() + action_block + "\n", encoding="utf-8")

if youtube_urls:
    YT_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "-", task_id).strip("-")[:80] or "task"
    research_path = YT_DIR / f"{stamp}-{safe_id}.md"
    research_path.write_text(
        f"# Gemini YouTube araştırması\n\n"
        f"- Task: {task_id}\n"
        f"- Project: {project}\n"
        f"- Model: {MODEL}\n"
        f"- Created: {iso}\n"
        f"- URLs: {', '.join(youtube_urls)}\n\n"
        f"{reply}\n",
        encoding="utf-8",
    )

INBOX.write_text(
    "# Inbox → Gemini API\n\n"
    "Bu dosya Gemini API için genel amaçlı görev kutusudur.\n\n"
    "## TASK\n"
    "status: idle\n"
    f"id: {task_id}\n"
    "from: system\n"
    f"project: {project}\n"
    "url:\n"
    "prompt: |\n"
    f"  Son görev işlendi: {msg_id}\n",
    encoding="utf-8",
)

print(f"Gemini yanıtı kaydedildi: {msg_id}; {len(reply)} karakter")
