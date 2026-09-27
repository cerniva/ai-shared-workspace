# Cerno Shorts — araştırma / seçim modülü

Mevcut hattı silmez. Render ve yayın öncesine kapı ekler.

Korunan bileşenler:
- `scripts/shorts_preflight.py` (MP4 fail-closed gate)
- `scripts/youtube_upload.py` + `.github/workflows/youtube-upload.yml`
- Buffer taslak kuralı: otomatik public yayın yok
- HyperFrames / kredi harcayan render yalnızca paket `gate` geçtikten sonra

Akış:
ARAŞTIR → HAVUZ (≥5 fikir) → PUANLA (`shorts_research.py score`) → SEÇ → DOĞRULA
→ ÖZGÜN AÇI → HOOK → SENARYO → GÖRSEL/SES PLAN → `gate` → RENDER → preflight → kuyruk/yayın
→ performans kaydı (`decision-log.md`) → kaynak puanı (`source-pool.json`)

Komutlar:
```
python3 scripts/shorts_research.py score --input knowledge/shorts/candidates.json
python3 scripts/shorts_research.py check-duplicate --title "..." --hook "..."
python3 scripts/shorts_research.py gate --packet knowledge/shorts/packets/<id>.json
```

Yasak:
- rastgele konu ile doğrudan render
- tek kaynak
- “Merhaba arkadaşlar / Bugün size / Bu videoda” giriş
- clickbait vaat
- aynı hook/başlık/tekrar senaryo
- yayın öncesi preflight’sız upload
