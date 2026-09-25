# AIL Collective v2 Architecture

Principle: do not fake automation.

## Canonical sources (Phase 2 files)

| Entity | Source |
|--------|--------|
| Human AIL chat | GitHub Issues/comments |
| Orchestrator message copy | data/messages/{id}.json |
| Delivery | data/relay/{id}.json |
| Tasks | data/tasks/{id}.json |
| Agents | data/agents.json |
| Audit | data/audit/{id}.json |
| Knowledge | knowledge/*.md |
| Outputs | outputs/* |

GitHub files are not a queue. One record per file. Writers use blob SHA.

## Status

Schema locked for Phase 2 review. Runtime worker is not live. Fake-adapter fixture is data only.
