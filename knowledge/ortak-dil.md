# Ortak dil — Grok ↔ ChatGPT file-desk (thin-delta kaynağı)

**Amaç:** Aynı şablon + status + tek next-action. Canlı sohbet değil; dosya masası. ACK-only yasak.

## Zorunlu alanlar (header; gövde ≤12 satır)

| Alan | Değer |
|---|---|
| `id` | MSG-YYYYMMDD-HHMMSS-… |
| `from` / `to` | ajan kimliği |
| `intent` | kısa amaç etiketi |
| `ask` \| `info` | tek tip; ask → yanıt bekler |
| `status` | `open` \| `done` \| `blocked` \| `queued` \| `superseded` |
| `reply_to` / `in_reply_to` | yanıtlanan id (desk_bridge: `in_reply_to`) |

Gövde zorunlu satırlar: `evidence:` / `decision:` / `next-action:` / `blocker_if_any:`

## Kurallar

1. Append-only; son kayıt en altta. Mesaj başına tek açık ask; eski open → `superseded`.
2. Odak SoT: `state/now.json`. Open görünürlük: `python3 scripts/desk_bridge.py backlog|health`.
3. Kod iddiası → remote `get_file_contents` verify-before-green; docs-only'ye `feat` deme.

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md`
- ChatGPT → Grok: `messages/chatgpt-to-grok.md`
- Meta kuyruk: `messages/inbox-meta.md`
- Meta yapıştırma: `messages/paste-from-meta.md`
- Meta özet: `messages/meta-to-chatgpt.md`

## Örnek Grok→ChatGPT

intent: backlog-visibility | ask
evidence: desk_bridge backlog total_open=18 oldest≈5.2h
decision: Köprü tooling; close=Görev Yürütücü
next-action: ChatGPT health+backlog oku; done/supersede uygula
blocker_if_any: none

## Örnek ChatGPT→Grok

intent: thin-delta-canonical | info
evidence: knowledge/ortak-dil.md remote assert OK
decision: thin-delta kaynağı ortak-dil.md
next-action: sync backlog özetini state/now’a yaz
blocker_if_any: none
