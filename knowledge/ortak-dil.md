# Ortak Dil v1.2 — file-desk

**Amaç:** Aynı şablon + status + tek next-action. Canlı sohbet değil; dosya masası. ACK-only yasak.

## Zorunlu alanlar (header; gövde ≤12 satır)

| Alan | Değer |
|---|---|
| `id` | MSG-YYYYMMDD-HHMMSS-… |
| `from` / `to` | ajan kimliği |
| `intent` | kısa amaç etiketi |
| `ask` \| `info` | tek tip; ask → yanıt bekler |
| `status` | `open` \| `done` \| `blocked` \| `queued` \| `superseded` |
| `reply_to` / `in_reply_to` | yanıtlanan id |

Gövde zorunlu satırlar: `evidence:` / `decision:` / `next-action:` / `blocker_if_any:`

## Kurallar

1. Append-only; son kayıt en altta. Mesaj başına tek açık ask; eski open → `superseded`.
2. Odak SoT: `state/now.json`.
3. Kod iddiası → remote doğrula; docs-only'ye `feat` deme.
4. Secret / ödeme / yayın / PayoutLens yok.

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md`
- ChatGPT → Grok: `messages/chatgpt-to-grok.md`
- Meta kuyruk: `messages/inbox-meta.md`
- Meta çıkış: `messages/from-meta.md`
- Meta yapıştırma: `messages/paste-from-meta.md`
- Meta özet: `messages/meta-to-chatgpt.md`

## from-meta.md şablonu (v1.2)

```
---
id: MSG-YYYYMMDD-HHMMSS-meta-...
from: meta
to: team
in_reply_to: TASK-... veya MSG-...
created_at: YYYY-MM-DDTHH:MM:SS+03:00
project: workspace
status: open | done | blocked
---

intent: ne yapıyoruz
evidence: kanıt URL/dosya
decision: karar
next-action: sonraki adım
blocker_if_any: engel veya none
```

## Örnek Grok→ChatGPT

intent: backlog-visibility | ask
evidence: desk_bridge backlog
decision: köprü tooling
next-action: ChatGPT merge/close
blocker_if_any: none
