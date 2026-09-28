# Google + YouTube Source Routing Verification Notes

Date: 2026-09-28
Branch: `chatgpt/google-youtube-source-routing-design`

## Live connector evidence

- TinyFish Search returned official YouTube/Google Help results; TinyFish Fetch read the public Google and YouTube surfaces.
- vidIQ zero-credit owned-channel read returned an authorized channel; no account identifier is persisted in repo state.
- Metricool brand settings returned a connected YouTube network; no account identifier is persisted in repo state.
- Google Research and YouTube Studio Browser Context Profiles remain `setup-unverified` because no profile-backed authenticated Studio read was executed solely for status verification.
- Direct YouTube OAuth `invalid_grant` remains a separate blocker; Metricool/vidIQ connectivity does not close it.

## External automation read-back

Five active automations were updated by prompt only and read back successfully:
- Email Monitor
- Bilgi Kütüphanesi
- Finans
- Video, Shopify ve Sistem Geliştirmeleri
- Sistem Kaynak Araştırması

For all five, enabled state, hourly schedule and timing mode were preserved. Prompts now share source-routing, dedup and evidence rules without storing credentials or browser-session material.

## Main-branch reconciliation

Before opening the PR, current `main` was three commits ahead of the feature branch merge base. The three commits were inspected: two only refreshed `state/worker_health.json`; one added `knowledge/system-sources/playwright-auto-waiting-2026-09-28.md`. None modified the files changed by this branch, so no same-path overwrite was required.

## Merge gates

- PayoutLens paths must not appear in the PR diff.
- Direct YouTube OAuth blocker must remain in `state/now.json`.
- Browser Context Profiles must remain setup-only until a real authenticated run/read proves them.
- Repository CI/review is the final validation gate because this connector-only session cannot execute the repository test suite in a local checkout.
