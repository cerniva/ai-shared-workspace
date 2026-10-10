# messages/apps/github-copilot.md — GitHub Copilot uygulama kanalı (append-only)

Rol: GitHub'da kod/PR. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.
Not: Microsoft Copilot (Office/Outlook) ayrı kanaldır: `messages/apps/copilot.md`.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: PR linki, commit SHA, issue numarası veya Actions run. Kanıtsız `done` yok.
- Copilot cloud agent çıktısı PR'dır; `main` merge kararı ChatGPT'dedir. Kayıt elle aktarılırsa `from: github-copilot (via furkan)` yazılır.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-GHCOPILOT-YYYYMMDD-HHMM>
id: APP-GHCOPILOT-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|github-copilot
to: github-copilot|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / PR / issue / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
