# messages/apps/perplexity.md — Perplexity uygulama kanalı (append-only)

Rol: araştırma, zamanlanmış görev. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.
Not: Bu kanal consumer Perplexity uygulaması/Computer içindir; API worker kuyruğu ayrıdır (`messages/inbox-perplexity.md`).

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: commit SHA, dosya yolu, URL veya message_id. Kanıtsız `done` yok.
- Perplexity bu dosyaya doğrudan yazamıyorsa yanıtı Furkan elle yapıştırır ve `from: perplexity (via furkan)` yazar.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-PERPLEXITY-YYYYMMDD-HHMM>
id: APP-PERPLEXITY-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|perplexity
to: perplexity|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / yol / URL / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
