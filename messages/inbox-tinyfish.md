# inbox-tinyfish — ChatGPT/Grok → TinyFish fetch kuyruğu

Worker: `.github/workflows/tinyfish-senses.yml` → `scripts/tinyfish_senses.py`
Çıkış: `messages/from-tinyfish.md`
Secret: `TINYFISH_API_KEY` (sohbete yazılmaz)
Mod: fetch-only. Agent/Browser/login/publish yok.

## TASK
status: queued
id: CORE-04-TF-STOREFRONT-20260926
from: grok
to: tinyfish
created_at: 2026-09-26T17:05:00+03:00
project: shopify
urls: https://i19cci-4e.myshopify.com
prompt: |
  Public storefront fetch only. Report password wall vs catalog. No login, no click, no payment.
