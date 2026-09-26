# Inbox → Gemini API

Bu dosya Gemini API için genel amaçlı görev kutusudur.

## TASK
status: queued
id: CORE-05-PUBLIC-SYSTEM-REVIEW-20260926
from: chatgpt
project: workspace
use_shopify: false
use_youtube_analytics: false
context_files: scripts/gemini_senses.py, scripts/enrich_context.py, .github/workflows/gemini-senses.yml
url:
prompt: |
  Ortak çalışma sisteminin halka açık kod ve protokol katmanını ikinci gözle incele.
  Önceliğin yanlış başarı raporu, boşa tekrar çağrı, gizli veri sızıntısı ve
  kullanıcıya gereksiz kurulum çıkarmayan somut iyileştirmeler olsun.
  Özel Shopify veya YouTube Analytics verisi isteme; secret isteme.
  Mevcut işçi ve kuyruk modeline uygulanabilir kısa öneri ver.
