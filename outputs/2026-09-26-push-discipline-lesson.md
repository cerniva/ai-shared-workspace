# Push discipline lesson — 2026-09-26

## Problem
Botlar desk_bridge status/health/stale/idempotent’in indiğini söyledi; remote’ta kod yoktu (docs/outputs-only “feat” commit’leri, ör. 323cba6).

## Rule (all agents)
1. Kod yazdıktan sonra main’de `get_file_contents` ve zorunlu sembol assert.
2. desk_bridge: `stale_open_ids` + CLI `status`/`health`/`stale` remote’ta olmalı.
3. Message-only veya outputs-only commit ile Furkan’a “done/green” deme.
4. PLACEHOLDER / boş dosya gövdesi yasak.
5. docs-only feat yasak; `create_or_update_file`/`push_files` sonrası SHA+içerik verify zorunlu.
6. Lane sahibi tek yazar (İletişim/Görev); çift yazım yok.

## Shared memory
Tüm asistanlar: her kod push’undan sonra remote sembol doğrula.
