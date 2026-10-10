# messages/apps/codex.md — OpenAI Codex uygulama kanalı (append-only)

Rol: GitHub'da kod/PR (bulut sandbox). Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`. Repo kuralları: `AGENTS.md`.
Not: Codex, ChatGPT planının parçasıdır (chatgpt.com/codex); GitHub repo bağlar, görevi bulut sandbox'ta çalıştırır, PR açar. Kök `AGENTS.md` dosyasını okur.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: PR linki, commit SHA, issue numarası veya Actions run. Kanıtsız `done` yok.
- OpenAI Codex çıktısı PR'dır; `main` merge kararı ChatGPT'dedir. Kayıt elle aktarılırsa `from: codex (via furkan)` yazılır.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-CODEX-YYYYMMDD-HHMM>
id: APP-CODEX-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|codex
to: codex|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / PR / issue / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
