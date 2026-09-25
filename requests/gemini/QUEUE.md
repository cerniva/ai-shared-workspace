# Gemini request queue

Bir istek = bir dosya: `requests/gemini/REQ-YYYYMMDD-HHMMSS.md`

Şablon:

```
---
id: REQ-...
from: grok | chatgpt | human
project: youtube | finance | content | shopify | workspace
url:
status: queued
---

Görev metni.
```

`status: queued` olan dosyalar Action tarafından işlenir.
