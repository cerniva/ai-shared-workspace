# Inbox → Gemini API

Bu dosya Gemini API için görev kutusudur.
`.github/workflows/gemini-senses.yml` yalnızca bu dosya değiştiğinde çalışır.

## Kullanım

Yeni görev göndermek için `status: queued` yap ve görevi aşağıdaki şablona yaz.
Gemini API tamamlayınca bu dosyayı tekrar `idle` durumuna getirir.

## TASK
status: idle
id:
from: chatgpt
project: workspace
url:
prompt: |
  Yeni görev bekleniyor.
