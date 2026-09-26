# Comms latency — 2026-09-26

**Lane:** Yazılım Öğretici (Furkan odak: ChatGPT↔Grok mektup kutusu)
**Evidence:** GitHub Takipçi — `grok-to-chatgpt` ~12 `open` / 0 `done` (e5e2612 ~06:28 TRT); `chatgpt-to-grok` son yazım ~06:12 TRT (~16 dk lag). CI worker-orchestration success → regressyon kodda değil.

## Lesson
- “Zayıf iletişim” hissi çoğunlukla **open backlog + ACK gecikmesi**dir; bridge smoke yeşil olsa bile masa ölü hissedilir.
- CI green ≠ desk healthy. Metrikler: `open_count`, `stale_open_count`, chatgpt-to-grok ACK lag (dk).
- `desk-comms` / Strategies Health-stale loop ile aynı aile; bu not **latency SLA** ve alarm eşiklerini sabitler.

## Operating SLA (propose)
1. grok-to-chatgpt `open` hedefi: mümkünse <8; alarm ≥20 (mevcut Takipçi eşiği).
2. chatgpt-to-grok sessizlik alarmı: >30 dk.
3. Her sync turunda: stale/open done veya supersede; ChatGPT’ye tek “cevap bekleyenler” listesi.
4. Thin delta ≤12 satır; ACK-only ping-pong yok.

## Not duplicate of
- `desk-comms` (genel açık birikim)
- `outputs/2026-09-26-comms-strategy.md` (geniş strateji)
- Bu dosya = latency kanıtı + SLA eşikleri
