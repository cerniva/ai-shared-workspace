# CORE-02 finance report spec

Status: canonical
Updated: 2026-10-02T13:20:00+03:00
Scope: report rules only. This file does not publish prices, news, or trade advice.

## Why this file exists

Before this record, finance rules were scattered and incomplete:

- `tasks/active.json` CORE-02 only names the standing task.
- `projects/finance/` contained only `.gitkeep`.
- `research/SOURCES.md` has a 2026-09-27 primary-source table. That table is a human index, not the presentation spec.
- `knowledge/RESEARCH_ROUTER.md` requires primary sources and a second check for finance claims. It does not define report layout.
- Code search on main `9de468ec527434b31cb39f8c0b82e02312fc5ec8` returned no `Base-100` and no `CHAT GPT ANALİZİ`.

Do not delete those older notes. This file is the presentation and scope canonical record. Machine twin: `projects/finance/report_spec.json`.

## Scope

A finance report may cover only the classes below. Omit a class when there is no new verified evidence; do not invent a reading for it.

- precious metals
- energy and oil
- industrial metals
- crypto
- equities and indices
- bonds and rates
- funds and ETFs
- FX
- macro and calendar
- finance-related world news

PayoutLens is out of scope.

## Presentation

- Default report is chartless. The latest user preference is no chart unless a chart is explicitly requested again.
- Do not generate charts with Python.
- Base-100 and separate metals/crypto charts are historical layout rules, not the default.
- Altcoin Boğa Paneli is off by default. If charts are requested again, that panel keeps two panels, each normalized 0-100 on bullish-support. Do not collapse them into one series.
- Every finance report ends with the exact line `CHAT GPT ANALİZİ:`.
- Separate verified fact, retrieval time, and opinion. Do not present a forecast as a fact.

## Sources

- Reuse `research/SOURCES.md` section `Finans ve piyasa için birincil kaynaklar — 2026-09-27` before adding a source.
- A unique real source belongs in `knowledge/source_catalog.json` through `scripts/knowledge_bridge.py`, with access status proven by a real fetch. Listing a URL here is not a new access proof.
- Do not fabricate live prices, headlines, or source access.
- Plugin names in old reports are not verified connections.

## Non-goals

This spec does not start an hourly market fetch, does not rewrite the source catalog, and does not merge PR #99 or retry issue #101.
