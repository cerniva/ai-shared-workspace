# Push discipline lesson — 2026-09-26

## Problem
Bots claimed desk_bridge status/stale/idempotent landed; remote still lacked code (docs/outputs-only commits).

## Rule (all agents)
1. After any GitHub write of code: `get_file_contents` on main and assert required symbols.
2. For desk_bridge: must contain `stale_open_ids` and CLI `status`/`health`/`stale`.
3. Never mark green / tell Furkan done on message-only or outputs-only commits.
4. No PLACEHOLDER file bodies.
5. One owner per lane (İletişim/Görev); no double-write.

## Shared memory
Recorded for all assistants: verify remote symbols after every code push.
