# Playwright auto-waiting and locator reliability

- Source: https://playwright.dev/docs/actionability
- Companion: https://playwright.dev/docs/locators
- Evidence tier: official
- Access: verified-public
- Verified: 2026-09-28
- Category: browser-automation-reliability

## Gap closed
The shared catalog already covers GitHub CI concurrency, API rate-limit backoff, cache, artifact provenance, and workflow timeouts, but it had no browser-level reliability guidance for DOM timing and selector stability.

## Operational guidance
For browser automation implemented with Playwright, prefer Locator-based actions and web-first behavior rather than fixed sleeps/manual polling. Playwright performs actionability checks before actions and auto-waits until the checks pass or the configured timeout is reached. Locators are the core of this retry/auto-wait behavior; prefer user-facing/accessibility locators such as role, label, text, placeholder, alt text, title, or explicit test IDs when appropriate.

## Why it matters to CORE-05
This reduces a concrete browser-worker failure class: flaky interactions caused by racing page rendering/animation/enablement. It complements, rather than replaces, the existing outer GitHub Actions `timeout-minutes` guard. Browser action timeouts should remain bounded so a bad page fails instead of hanging the worker.

## Limits
This guidance applies when Playwright is actually used. It does not make arbitrary websites stable, bypass CAPTCHA/login/MFA, authorize destructive actions, or replace application-level retry policy, workflow timeouts, cleanup, evidence capture, or a fallback provider. Do not add Playwright solely because this source exists; use it only where the existing browser path has a verified gap.

## Dedup evidence
Checked `knowledge/source_catalog.json` and repository search for Playwright/locator/browser-timeout/OpenTelemetry terms before adding. No existing Playwright reliability source was present. PayoutLens was not modified.
