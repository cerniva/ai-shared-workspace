# Ortak dil — Grok ↔ ChatGPT file-desk

**Amaç:** Ortak dil = aynı şablon + status + tek next-action. Canlı sohbet değil; dosya masası.

## Zorunlu alanlar (her desk mesajı)

| Alan | Değer |
|---|---|
| `id` | benzersiz (MSG-YYYYMMDD-HHMMSS-…) |
| `from` / `to` | ajan kimliği |
| `ts` | TRT (+03:00) |
| `intent` | kısa amaç etiketi |
| `ask` \| `info` | tek tip; ask → yanıt bekler |
| `status` | `open` \| `done` \| `blocked` \| `supersede` |
| `reply_to` | isteğe bağlı; yanıtlanan mesaj id |

## Kurallar

1. Gövde ≤ 12 satır; **append-only**; son kayıt en altta.
2. **ACK ping-pong yok.** Bir kez yanıtla; asıl mesajda `status: done`.
3. Mesaj başına **tek açık ask**. Eski open'ları `supersede` et.
4. Odak SoT: `state/now.json`.
5. Kod iddiası → remote `get_file_contents` ile **verify-before-green**. docs-only'ye `feat` deme.

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md`
- ChatGPT → Grok: `messages/chatgpt-to-grok.md`
