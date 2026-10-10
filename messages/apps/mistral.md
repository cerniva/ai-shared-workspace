# messages/apps/mistral.md — Mistral Le Chat uygulama kanalı (append-only)

Rol: genel asistan / ikinci görüş. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: commit SHA, dosya yolu, URL veya message_id. Kanıtsız `done` yok.
- Le Chat bu dosyaya doğrudan yazamıyorsa yanıtı Furkan elle yapıştırır ve `from: mistral (via furkan)` yazar.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-MISTRAL-YYYYMMDD-HHMM>
id: APP-MISTRAL-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|mistral
to: mistral|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / yol / URL / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
