# inbox-meta — ChatGPT/Grok → Meta görev kuyruğu

Worker: `.github/workflows/meta-senses.yml` → `scripts/meta_senses.py`
Çıkış: `messages/from-meta.md`
Secret: `META_MODEL_API_KEY` (sohbete yazılmaz)

Çalışması için gövde satırı: `status: queued` veya `status: open`.
İş yokken: `status: idle`

Format: her görev bu şablonda. Append-only, son kayıt en altta.

## TASK
status: queued
id: CORE-05-META-CAPABILITY-PLAN-20260926
from: chatgpt
to: meta
created_at: 2026-09-26T15:54:00+03:00
project: workspace
task: multi-agent-automation-plan
prompt: |
  Furkan asks the four assistants to plan requirements for a real AI automation system. Review the provided Meta AI share proposal and the existing repo bridge context if available. Assess only what your actual API can do; do not claim browser access unless verified. Report: existing pieces, what the Meta AI web share does not provide, safe minimal architecture, exact blockers/user actions. No code changes, no secrets, no PayoutLens, no Shopify writes.

# Re-trigger after the API secret was added (2026-09-26).