# messages/apps/genspark.md — Genspark uygulama kanalı (append-only)

Rol: araştırma/rapor. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: commit SHA, dosya yolu, URL veya message_id. Kanıtsız `done` yok.
- Genspark bu dosyaya doğrudan yazamıyorsa yanıtı Furkan elle yapıştırır ve `from: genspark (via furkan)` yazar.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-GENSPARK-YYYYMMDD-HHMM>
id: APP-GENSPARK-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|genspark
to: genspark|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / yol / URL / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
