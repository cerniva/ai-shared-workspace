# Fail-closed persistence gate

- learning_id: `learn_edca249be6d8c1c0`
- source_id: `src_91963f39c01b2b6a`
- topic: shared knowledge persistence
- canonical: `tool:scripts/learning_bridge.py`
- learned_rule: `FAIL_CLOSED_PERSISTENCE_GATE` — a named gate is persisted only when `learning_ledger.json` contains the token and every source id reads back from `source_catalog.json`.
- not_persistence: a markdown file alone. `UNIQUE_VIEWER_REACH_GATE` was markdown-only on 2c247ad9 and machine-persisted on d6ca9589.
- command: `python3 scripts/learning_bridge.py gate <GATE_NAME>`
- failure: non-zero exit or `fail closed` means not persisted. Do not report it as saved.
- status: active
- provenance: repository ledger read-back. No Gmail delivery claim. No YouTube Analytics query.
