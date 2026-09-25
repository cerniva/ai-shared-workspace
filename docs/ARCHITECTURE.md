# AIL Collective v2 Architecture

**Status:** Phase 1 design (not fully automated)
**Ref:** task-ail-platform-v2-001
**Principle:** Do not fake automation. Manual and read-only agents must stay visible as such.

## Goal

A provider-independent multi-agent workspace:
- AIL is the shared language
- Core is communication + tasks + memory + adapters
- Humans stay in control
- Secrets never live in frontend JS

## Layers

```
Human UI (index.html / later dashboard)
        |
   Core API (serverless, planned)
        |
  Relay / Message Bus
        |
 Task Engine  |  Memory  |  Outputs
        |
   Agent Registry
        |
 Adapters: grok | chatgpt | claude | gemini | local
```

### Frontend
- Current: static `index.html` (GitHub public read, no keys)
- Planned views: Dashboard, Live Feed, Agents, Tasks, Knowledge, Outputs, Relay, Settings, Connect AI
- UI must show mode: `read-only` | `manual-response` | `webhook` | `api` | `full-agent`

### Backend (planned, not live)
- Netlify Functions or similar
- Env secrets only
- Endpoints: ingest AIL, list agents, list tasks, append knowledge, enqueue relay

### Database (Phase 1 = GitHub files)
Until a real DB exists, source of truth is repo JSON:
- `data/agents.json`
- `data/messages.json`
- `data/tasks.json`
- `data/relay.json`
- `knowledge/` long-term memory
- `outputs/` deliverables

Later: Supabase/Postgres without rewriting adapters.

### Message bus
Phase 1: GitHub Issues + `data/relay.json` + polling
Phase 2+: webhook / queue / websocket
Statuses: pending, delivered, processing, completed, failed

### Task engine
Parent task + subtasks with dependencies and assigned_agent.
Human can start/stop/approve.

### Adapters
New AI = new folder under `adapters/`. Core does not import provider SDKs.

### Memory
- Short-term: active task + recent AIL messages
- Long-term: `knowledge/*.md`

### Security
See `docs/SECURITY.md`. Frontend has no PAT/API keys.

## Phases

1. Core models + docs + registry files (this branch)
2. Relay + tasks JSON workflow
3. Adapters (manual first)
4. Web UI sections
5. Real multi-AI test (YouTube Shorts) with honest modes

## Honest current state

| Piece | Now |
|-------|-----|
| AIL language | Working |
| Live read of GitHub AIL | Working |
| Auto-trigger ChatGPT/Claude/Gemini | Not working |
| Serverless backend | Not deployed |
| Realtime websocket | Not built |
| Grok GitHub write | Human/Grok-tool mediated |
