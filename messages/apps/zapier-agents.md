# messages/apps/zapier-agents.md — Zapier Agents uygulama kanalı (append-only)

Rol: otomasyon. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: commit SHA, dosya yolu, URL, run linki veya message_id. Kanıtsız `done` yok.
- Zapier Agents bu dosyaya doğrudan yazamıyorsa yanıtı Furkan elle yapıştırır ve `from: zapier-agents (via furkan)` yazar.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-ZAPIER-YYYYMMDD-HHMM>
id: APP-ZAPIER-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|zapier-agents
to: zapier-agents|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / yol / URL / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
