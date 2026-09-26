# Inbox → Meta AI (insan köprüsü)

Mod: file-desk. Meta sohbet worker yok; API worker ayrı belgede (`docs/META_WORKER.md`).
Furkan `prompt` u Meta AI'ya taşır. Sonucu `messages/paste-from-meta.md` ye yapıştırır.

Akış:
1. Grok veya ChatGPT buraya `status: queued` görev yazar
2. Furkan prompt'u Meta AI sohbetine kopyalar
3. Meta cevabını `messages/paste-from-meta.md` altına yapıştırır
4. Grok/ChatGPT paste'i okur, özeti `messages/meta-to-chatgpt.md` ye append eder

## TASK
status: idle
id:
from:
project:
allowed_actions: public-web-read | form-fill-draft | screenshot-evidence | research-synthesis
forbidden: login-secret | payment | publish | irreversible-write | PayoutLens
prompt: |
  (boş — ChatGPT veya Grok queued görev yazar)
