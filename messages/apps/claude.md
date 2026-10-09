# messages/apps/claude.md — Claude uygulama kanalı (append-only)

Rol: kod inceleme. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: commit SHA, dosya yolu, URL veya message_id. Kanıtsız `done` yok.
- Claude bu dosyaya doğrudan yazamıyorsa yanıtı Furkan elle yapıştırır ve `from: claude (via furkan)` yazar.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-CLAUDE-YYYYMMDD-HHMM>
id: APP-CLAUDE-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|claude
to: claude|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / yol / URL / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
