# Inbox-first work order — 2026-09-26

**Lane:** Yazılım Öğretici (Furkan standing order + Grok düzeltmesi)
**Evidence:** research-bot EVET (`063500`) masada yazılmış ama okunmamıştı; `064500` notify pending; unread≫0 / last_read yok → yazmak ≠ teslim.

## Lesson
- **write ≠ delivered until poll.** Dosyaya append = mektup kutuya bırakmak; alıcı okuyana kadar iletişim yok.
- **Bağlayıcı 2 adım (sıra sabit):**
  1. Mesaj kutusu kontrol + tek satır rapor
  2. Raporları oku + uygulamaya geç
- **Yanlış / superseded:** «Tabloları (BOARD/now/tasks) değerlendir» — Furkan iptal etti; kullanma.

## Operating rules
- Tur başı: karşı kanalı oku (Grok → `chatgpt-to-grok.md`; ChatGPT → `grok-to-chatgpt.md`).
- Pending → görüldü → cevap → bildirim kapanır; aynı MSG’ye tekrar uyarı yok; cevapsız → delayed escalate.
- Inbox okunmadan claim/commit = ihlal (Takipçi alarmı).
- Kod/health: İletişim Köprüsü; docs: Görev Yürütücü; ders: bu not + ledger `inbox-watch` / `two-step-work`.

## Not duplicate of
- `inbox-watch` (ledger): write≠delivered until poll
- `comms-latency` / `ortak-dil`: gecikme SLA + thin-delta şablonu
- Bu dosya = **2 adımlı iş sırası** + «tablo değerlendir» iptali
