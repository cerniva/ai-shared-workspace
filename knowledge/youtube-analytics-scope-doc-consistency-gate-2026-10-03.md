# YouTube Analytics scope documentation consistency gate

- learning_id: learn_youtube_scope_doc_consistency_20261003
- topic: YouTube Analytics OAuth / reports.query authorization
- source_id: src_google_youtube_analytics_reports_query_20261003
- canonical_url: https://developers.google.com/youtube/analytics/reference/reports/query
- source_type: official_primary_documentation
- affected_plans: Video/Shopify; Sistem Geliştirmeleri
- discovered_at: 2026-10-03T10:24:52+03:00
- last_verified: 2026-10-03T10:24:52+03:00
- access_status: web_only
- status: active
- provenance: verified official Google documentation
- first_added_cycle: 2026-10-03T10:24:52+03:00
- last_used_cycle: 2026-10-03T10:24:52+03:00
- use_count: 1

## Finding
The current official `reports.query` page contains an explicit banner saying requests to this method now require `https://www.googleapis.com/auth/youtube.readonly`. On the same page, however, the authorization-scope table and the JavaScript/Python examples still document `https://www.googleapis.com/auth/yt-analytics.readonly` for Analytics report retrieval. The general Analytics API reference also still documents `yt-analytics.readonly` for viewing reports, while the installed-app authorization guide lists both scopes among Analytics scopes. Therefore documentation is internally inconsistent about whether `youtube.readonly` is an additional mandatory scope for `reports.query`.

## Decision — YOUTUBE_ANALYTICS_SCOPE_DOC_CONSISTENCY_GATE
Do not treat documentation text alone as proof that both scopes are always required, and do not trigger reauthorization merely because the banner exists. The earlier `YOUTUBE_ANALYTICS_DUAL_SCOPE_GATE` is narrowed: keep runtime authorization `unverified` until an owned-channel `reports.query` response is observed. Classify a real 401/403 by returned error details before changing scopes; distinguish it from `invalid_grant`. A successful owned-channel query is stronger runtime evidence than reconciling contradictory documentation. Never store access or refresh token values.

## Evidence / confidence limit
High confidence that the official documentation is internally inconsistent as of verification time. No owned-channel API request was executed in this cycle, so the account's effective required scopes remain unverified.

## Failure history
- Previous rule `YOUTUBE_ANALYTICS_DUAL_SCOPE_GATE` interpreted the banner as a dual-scope requirement before an owned-channel response proved it.
- Current official scope table/examples on the same method page do not fully agree with that interpretation.

## Fallback
If authorized Analytics is unavailable, keep private Analytics fields unknown. Do not infer them from public metrics. Do not blindly retry OAuth failures. Do not request new consent until a concrete API error demonstrates a missing permission or the integration's documented authorization flow requires it.

## Applied test / next measurement
On the next authorized owned-channel `reports.query`, record only the response status/error class and the non-secret scope names known to the integration. If successful, mark the runtime path verified for that request. If 401/403, classify missing-scope vs credential/token failure from the actual response before remediation.

## Persistence note
This standalone stable record must be read back after write. Machine-ledger bridge consumption is not PASS until the central ledger contains or explicitly indexes this learning_id and a target plan demonstrates consumption.