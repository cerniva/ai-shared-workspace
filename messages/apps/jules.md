# messages/apps/jules.md — Google Jules uygulama kanalı (append-only)

Rol: GitHub'da kod/PR (Google VM). Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`. Repo kuralları: `AGENTS.md`.
Not: Jules (jules.google) GitHub repo bağlar, görevi VM'de çalıştırır, önce plan sunar, onaydan sonra branch/PR üretir. Kök `AGENTS.md` dosyasını okur.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: PR linki, commit SHA, issue numarası veya Actions run. Kanıtsız `done` yok.
- Google Jules çıktısı PR'dır; `main` merge kararı ChatGPT'dedir. Kayıt elle aktarılırsa `from: jules (via furkan)` yazılır.
- Secret, token, şifre bu dosyaya yazılmaz.

```
### <id: APP-JULES-YYYYMMDD-HHMM>
id: APP-JULES-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|jules
to: jules|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / PR / issue / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
