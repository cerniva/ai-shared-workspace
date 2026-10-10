# Grok bot / credit failover audit — 2026-10-10
status: VERIFIED_CODE_NOT_LIVE_FAILOVER
scope: cerniva/ai-shared-workspace; PayoutLens excluded
## Evidence read on main
- docs/PROVIDER_DEGRADATION_POLICY.md separates Grok chat, Grok API worker, and Grok Bot quota; do not conflate.
- scripts/provider_config.py: FAILOVER_ORDER=(gemini,openai,grok,meta,claude,deepseek,perplexity); only configured API credentials instantiate adapters. Grok credit failure does not imply another provider works.
- scripts/run_next_worker.py: selects queued/retryable/expired-lease work; worker selector currently limits worker to openai/chatgpt/any/None, so a task assigned to grok specifically may not be eligible for this runner.
- scripts/grok_fallback_channel.py: GitHub-file messages, not AI inference; delivered only after main commit plus receiver ack.
- messages/fallback/FB-20261009-213204-grok-fallback-open.json: Grok→ChatGPT unacknowledged message, not proof of live push.
- tests/test_provider_auth_failover.py: test_grok_403_does_not_block_next_provider uses MockAdapter(meta); demonstrates unit contract, not credentialed production fallback.
- reports/2026-10-08-grok-102-issue101-failover.md: 11 focused tests and 282 overall reported then; historical evidence, not re-run in this audit.
- docs/MULTI_AGENT_AUTOMATION_STATUS.md (dated Sep 29): says Gemini primary, local planner when cloud fails, TinyFish/Firecrawl web route; stale for present provider health.
## Conclusion
Code-level fallback exists and 403 handling has a regression test. No current live provider health/credit availability or 24/7 bot activity verified. File fallback messaging is separate from task execution. Do not advertise seamless Grok Bot quota handoff until an end-to-end workflow proves it.
## Small next test (no spending)
1. Add/execute deterministic mock test with Grok ProviderAuthError or quota failure, next healthy MockAdapter, and task state persistence read-back.
2. Test all providers unavailable -> bounded BLOCKED without retry storm; confirm no task loss.
3. Test grok-assigned queued work is either explicitly routed to eligible fallback or remains blocked with accurate reason (no silent starvation).
4. Only after mocked tests pass, optional credentialed smoke with already-configured zero-cost provider and explicit quota guard; collect run URL, SHA, outputs.
No secret reads or new paid services, no publishing, no main changes.
