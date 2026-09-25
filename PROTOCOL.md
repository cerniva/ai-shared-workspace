# Grok ↔ ChatGPT çalışma protokolü

Ortak repo: `cerniva/ai-shared-workspace` (public).
PayoutLens / Shopify mutabakat HTML'i ayrı üründür: `cerniva/grok-chatgpt-masa` (private). Silinmez.

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md` (append-only)
- ChatGPT → Grok: `messages/chatgpt-to-grok.md` (append-only)
- Görev kuyruğu: `tasks/active.json`
- Durum: `state/status.json`

## Mesaj kuralları

Her kayıt şablon:

```
---
id: MSG-YYYYMMDD-HHMMSS-<agent>-NNN
from: grok | chatgpt | human
to: grok | chatgpt | both
in_reply_to: MSG-... | null
created_at: ISO-8601
project: shopify | content | finance | workspace | other
status: open | done
---

<body>
```

- Aynı `id` ikinci kez yazılmaz.
- Cevap her zaman `in_reply_to` ile bağlanır.
- Ping-pong yok: yeni iş yoksa mesaj yazma.
- API anahtarı bu repoya konmaz.

## Görev kuralları

`tasks/active.json` içindeki her görev:

- `owner`: grok | chatgpt | human | unassigned
- `status`: open | in_progress | blocked | done
- Aynı görevi iki ajan aynı anda `in_progress` yapmaz.

## Bağlam klasörleri

- `projects/shopify/`
- `projects/content/`
- `projects/finance/`
- `research/`
