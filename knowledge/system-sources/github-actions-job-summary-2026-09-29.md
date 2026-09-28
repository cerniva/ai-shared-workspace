# GitHub Actions job summaries — CORE-05 feeder

- source_id: src_core05_github_step_summary_20260929
- canonical: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary
- evidence_tier: official
- verified_at: 2026-09-29T03:00:00+03:00
- category: github-actions-observability-cost

## Technical gap
CORE-05 has sanitized local JSONL and optional external observability sinks, but the current repository has no `GITHUB_STEP_SUMMARY` usage. Operators therefore may need to open raw logs/artifacts to see the most important CI outcome, increasing diagnosis time and encouraging unnecessary artifact retention/downloads.

## Verified capability
GitHub Actions supports per-step Markdown written to `GITHUB_STEP_SUMMARY`; GitHub groups step summaries into the workflow run's job summary. GitHub documents this specifically for surfacing important information such as test-result summaries without opening logs. Each step summary is isolated and limited to 1 MiB; upload failure does not fail the job.

## Decision value
Candidate for the CORE-05 execution queue: evaluate a small, sanitized job summary for worker/CI runs (result, failing check, bounded next action, artifact pointer) rather than adding another external observability service. This is a visibility/cost optimization, not a reliability fix by itself.

## Guardrails
- Do not write secrets, tokens, private page content, customer/order data, or raw browser traces into summaries.
- Keep existing machine-readable logs/artifacts as the source for detailed diagnostics; summary is an operator view only.
- Do not implement from this feeder; execution queue must assess the actual workflow and tests first.
- PayoutLens excluded.

## Dedup result
`knowledge/source_catalog.json` contained GitHub concurrency, API rate limits, cache, provenance, timeout, retention and Playwright diagnostics/resilience sources, but no job-summary source or equivalent operator-visible CI-summary decision. Repository code search for `GITHUB_STEP_SUMMARY` returned no match at verification time.
