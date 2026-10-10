# messages/apps/deepseek.md — DeepSeek uygulama kanalı (append-only)

Rol: kod/mantık. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.
Not: Bu kanal consumer DeepSeek sohbeti (chat.deepseek.com) içindir; API worker kuyruğu ayrıdır (`messages/inbox-deepseek.md`).

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: commit SHA, dosya yolu, URL veya message_id. Kanıtsız `done` yok.
- DeepSeek sohbeti repoya yazamaz; yanıtı Furkan elle yapıştırır ve `from: deepseek (via furkan)` yazar.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-DEEPSEEK-YYYYMMDD-HHMM>
id: APP-DEEPSEEK-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|deepseek
to: deepseek|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / yol / URL / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
