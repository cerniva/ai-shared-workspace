# YouTube Shorts metric-counting change — 2026-10-02

Status: verified primary-source learning candidate
Plan tags: Video/Shopify, Bilgi Kütüphanesi
Canonical source: https://support.google.com/youtube/answer/12220281
Source type: official YouTube Help
Checked: 2026-10-02T01:28:47Z

## Finding
Beginning 24 August 2026, YouTube counts a view when a video starts to play across Shorts, VOD and live. This counting change does not change YPP earnings/eligibility bases: Shorts earnings continue to use engaged Shorts views and YPP eligibility continues to use qualified Shorts views.

## Decision value
Do not interpret post-24-Aug-2026 raw Shorts views as directly comparable to the old counting regime without a methodology note. For production learning, prioritize owned engaged views, watch time/average view duration, retention and other relevant engagement evidence over raw starts alone.

## Confidence / limits
High confidence for metric semantics because the source is official YouTube Help. This does not prove that any specific hook, pacing, edit or topic causes higher retention; creative rules still require owned-channel analytics/tests.

## Intended use
Video/Shopify analytics and Bilgi Kütüphanesi source routing. When comparing historical Shorts performance across the 24-Aug-2026 boundary, annotate the metric-definition change and avoid treating raw-view deltas as pure content-performance deltas.

## Persistence note
This Markdown record is the backward-compatible human-readable layer. Promotion into `knowledge/source_catalog.json` and `knowledge/learning_ledger.json` must use the repository knowledge bridges or a full current-file read/update with blob-SHA serialization; never overwrite a truncated catalog response.