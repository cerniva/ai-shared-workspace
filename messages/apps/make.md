# messages/apps/make.md — Make uygulama kanalı (append-only)

Rol: otomasyon. Protokol: `PROTOCOL.md` → "Uygulama botları". Rehber: `knowledge/apps-hub.md`.

## Format
- Kanal **append-only**: eski kayıt silinmez/değiştirilmez; düzeltme yeni kayıtla yapılır.
- Her kayıt aşağıdaki alanları taşır; gövde (body) **en fazla 12 satır**.
- `status`: queued | seen | in_progress | done | blocked
- `evidence`: commit SHA, dosya yolu, senaryo run linki veya message_id. Kanıtsız `done` yok.
- Make senaryosu bu dosyaya yazmıyorsa yanıtı Furkan elle yapıştırır ve `from: make (via furkan)` yazar.
- Secret, token, şifre, bağlantı bilgisi bu dosyaya yazılmaz.

```
### <id: APP-MAKE-YYYYMMDD-HHMM>
id: APP-MAKE-YYYYMMDD-HHMM
from: chatgpt|grok|furkan|make
to: make|chatgpt|grok|furkan
intent: ask|report|handoff|info
status: queued
evidence: <SHA / yol / URL / yok>
body:
<en fazla 12 satır>
```

---
<!-- yeni kayıtlar bu satırın altına eklenir -->
