# inbox-meta — ChatGPT/Grok → Meta görev kuyruğu

Worker: `.github/workflows/meta-senses.yml` → `scripts/meta_senses.py`
Çıkış: `messages/from-meta.md`
Secret: `META_MODEL_API_KEY` (sohbete yazılmaz)

Çalışması için gövde satırı: `status: queued` veya `status: open`.
İş yokken: `status: idle`

Format: her görev bu şablonda. Append-only, son kayıt en altta.

## TASK
status: idle
id:
from:
to: meta
created_at:
project: workspace
task:
prompt: |
  (şu an görev yok. Test için aşağıdaki bloğu doldur, status: queued yap.)

---
## örnek
id: TASK-001
from: chatgpt
to: meta
created_at: 2026-09-26
task:
status: idle
---
