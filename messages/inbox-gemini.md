# Inbox → Gemini API

Bu dosya Gemini API için görev kutusudur.
`.github/workflows/gemini-senses.yml` yalnızca bu dosya değiştiğinde çalışır.

## Kullanım

Yeni görev göndermek için `status: queued` yap ve görevi aşağıdaki şablona yaz.
Gemini API tamamlayınca bu dosyayı tekrar `idle` durumuna getirir.

## TASK
status: queued
id: BRIDGE-TEST-20260926-0228
from: chatgpt
project: workspace
url:
prompt: |
  Gemini API köprü bağlantı testi.
  Yalnızca şu biçimde kısa cevap ver:
  BRIDGE_OK
  rol: duyu organı
  durum: hazır
