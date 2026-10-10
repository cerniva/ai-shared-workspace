# messages/apps/copilot.md — Microsoft Copilot uygulama kanalı (append-only)

Rol: Office/Outlook. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.
Not: GitHub Copilot ayrı kanaldır: `messages/apps/github-copilot.md`.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: commit SHA, dosya yolu, URL veya message_id. Kanıtsız `done` yok.
- Copilot repoya yazamaz; yanıtı Furkan elle yapıştırır ve `from: copilot (via furkan)` yazar.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-COPILOT-YYYYMMDD-HHMM>
id: APP-COPILOT-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|copilot
to: copilot|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / yol / URL / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
