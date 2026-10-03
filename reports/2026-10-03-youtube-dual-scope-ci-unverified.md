# YouTube dual-scope persisted CI still unverified

- status: CI_STILL_UNVERIFIED
- mail: [Task Update] Sistem Geliştirmeleri: YouTube dual scope persisted CI still unverified
- seen_reply_sent: 1a1007d6d33ca2f7 in thread 1a1007d1a6b10414
- rfc_in_reply_to: <oPiEJubUSeSkdA11ALx36w@geopod-ismtpd-22>
- bounce: not observed. noreply@tm.openai.com chat delivery not claimed. Sent is not delivered.
- payoutlens: untouched
- secrets: none

## Evidence

- Human knowledge commit 957a52c73e9084c9284e4059bb60a6033ffc2768 blob f28afc83.
- Source catalog commit 8283c35484a4fb023759bc442361fdc1fcb03dc5.
- Ledger commit 3bff9c5cbfc4485b8618c1a87c1f37ec7900d50d learning_id learn_a9a5c8d397ee3343.
- worker-orchestration-tests run 37103383435 on 3bff9c5c conclusion=failure. Job 111147121865. unittest FAIL test_desk_context.DeskContextHealthTests.test_documented_status_command_runs_directly. stdout: CORE-05 knowledge bridge: ERROR (CatalogError: unstable source_id: src_google_youtube_analytics_reports_query_20261003). Fail-closed persistence gate step skipped.
- desk-notify run 37103401063 on 976ee6fa conclusion=failure. Job 111147192788. git pull --rebase conflict in state/desk_notify_health.json against b7030e1. Later health file has ok=true, consecutive_failures=0, no conflict markers. Race, not an open merge conflict.
- Local validators after id rewrite: source_id src_1ee3fe3382f17f55 = sha256(canonical reports.query URL)[:16]; learning_id learn_c26dcb3fda0b6b0c = learning_id(domain, claim). Catalog validate 51. Ledger validate 31. Only this row was unstable.
- Markdown pointer commit e3ce46d4549778caffc1bd4474ce58a98c0d3641 records those stable ids. Catalog and ledger were not rewritten in that commit, so worker CI is not green yet.
- No owned-channel reports.query. Runtime authorization remains unknown, not verified_connected.

## Decision

CONSENSUS on the fail-closed dual-scope rule. DISAGREE that persistence CI is verified. Dated/human source_id fails knowledge_bridge.normalize_record. Sample scopes remain stale relative to the banner.

## Next

Rewrite knowledge/source_catalog.json and knowledge/learning_ledger.json to the stable ids, then read worker-orchestration-tests on that commit. Do not reauthorize until a missing youtube.readonly error is observed. Same mail not processed again.
