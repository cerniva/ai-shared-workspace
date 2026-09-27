# Yapıştırma kutusu — Meta AI → masa

Furkan buraya Meta AI sohbetinden kopyaladığı metni yapıştırır.
Grok/ChatGPT bu dosyayı okur; gerekirse özeti `messages/meta-to-chatgpt.md` ye taşır.

Kurallar:
- Secret / şifre / token / kart / PayoutLens yok
- Login, ödeme, yayın, silme, geri döndürülemez yazma yok
- Ham yapıştırma yeterli; düzenleme şart değil
- İlgili görev id'sini biliyorsan üste yaz

---
status: ingested
id: META-PASTE-20260927-214900
from: user
source: https://meta.ai/share/c/ycDe8g6HQz
in_reply_to:
created_at: 2026-09-27T21:49:00+03:00
---

## PASTE BELOW THIS LINE

Title: Grok ve ChatGPT projeleri
Share: https://meta.ai/share/c/ycDe8g6HQz?utm_source=ios_cl
Captured: 2026-09-27T21:49+03 via Grok open_page + browser (logged-out share view).
ZIP attachment ortak-bilgi-havuzu-final.zip was listed in the share UI but not downloaded (no authenticated Meta session).

Visible Meta reply (Turkish):

Mükemmel, o 3 detayı ekledim - final versiyon hazır.

Senin eklediğin 3 kontrol noktasını entegre ettim:

1. GitHub Actions & Secrets

Final knowledge-sync.yml'e ekledim:

YAML
permissions:
  contents: write

concurrency:
  group: knowledge-base
  cancel-in-progress: false
(1 line hidden in share UI)

Senin dediğin gibi Settings > Actions > General > Workflow permissions > Read and write permissions aktif edilmeli, yoksa Meta AI INDEX.md'yi push edemez. Secret'lar için de OPENAI_API_KEY, GEMINI_API_KEY, XAI_API_KEY'i Secrets'e eklemen yeterli.

2. Kök Talimat

PROMPT.md final'de her ajana ilk talimat olarak tanımlı. ChatGPT için tetikleyici cümle:

"GitHub depomuzdaki knowledge/raw_insights/ dizinini incele, son eklenen verileri oku ve sonucunu knowledge/processed/ klasörüne kaydet."

Bu cümle öğrenme döngüsünü başlatıyor.

3. Çakışma Önleme

Senin önerdiğin gibi uyguladım:

- Dosya adı: YYYY-MM-DD_{agent}_{konu}.md → örn: 2026-09-27_gemini_yt-shopify.md
- Yetki: INDEX.md'yi SADECE Meta AI yazar, diğerleri sadece okur
- Concurrency: Aynı anda 4 ajan yazsa bile kuyruğa alır, merge conflict olmaz

Final paket:
ortak-bilgi-havuzu-final.zip

İçinde SETUP.md dosyası var - senin yazdığın 3 madde adım adım orada.

Private repo'yu açıp push ettiğinde:
- knowledge/raw_insights/ → Gemini/Grok besler
- knowledge/processed/ → ChatGPT sentezler
- INDEX.md → Meta AI curator günceller
- Actions log'dan canlı takip

Mimari tam senin dediğin gibi: ChatGPT'nin internet kısıtını Gemini aşıyor, git tabanlı versiyon kontrolüyle kolektif hafıza çelişkisiz büyüyor.

Log'da takılırsan at, beraber kontrol edelim.
