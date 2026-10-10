# messages/apps/n8n.md — n8n uygulama kanalı (append-only)

Rol: GitHub/Gmail otomasyon. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: commit SHA, dosya yolu, execution ID/URL veya message_id. Kanıtsız `done` yok.
- n8n workflow'u bu dosyaya yazmıyorsa yanıtı Furkan elle yapıştırır ve `from: n8n (via furkan)` yazar.
- Secret, token, şifre, credential bu dosyaya yazılmaz.

```
### <id: APP-N8N-YYYYMMDD-HHMM>
id: APP-N8N-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|n8n
to: n8n|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / yol / URL / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
