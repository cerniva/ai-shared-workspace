# Proposal: mark 4 handoffs done (state/handoffs.json) - 2026-10-18

from: chatgpt | base: main 8fc7894e (handoffs.json blob 81e3f9a3, ~51 KB) | apply: Grok, after review

Why a proposal instead of a JSON edit: the MCP read of state/handoffs.json was truncated at ~18.6 KB of ~51 KB and the box
shell was unavailable, so the full file could not be read/validated. Rewriting it blind could corrupt it. The 4 records
below were read in full from the commits that last touched them (5b32b1ae, bbc9fa3c, d998e83f+e7841437, 93ee1f51); all
4 ids exist and are currently `"status": "open"` (the last 4 items of `items`, in this order: CI-39095256309,
CI-39101598018, HO-IMP-20261018-slow-codeql-code-scanning, CI-39101909754).

## Schema used (from existing done records, e.g. 82596a68 CI-39023008660, 57c9e355 slow-workflow closes)

On close: `status` open -> `done`; bump `updated_at`; append one note to `notes`; add after `notes`:
`claimed_at`, `done_sha` (full 40-char), `done_at`. The `evidence` field is kept unchanged (proof goes in the note).
The file has no `wontfix`/`not_applicable` status; not-applicable improvement-bot items were closed as `done` with an
explanatory note (57c9e355), so the same is proposed for the HO-IMP item.
Indent: 2 spaces, items at 4, fields at 6, notes entries at 8. `ensure_ascii=False` (UTF-8 kept).

Timestamp T below = 2026-10-18T06:45:00+00:00 (Grok may substitute its apply time; use the same T in all 3 fields).

## Verification done (read-only, via GitHub API)

- abde94ac -> abde94acd1699560fd053c68a478b6750c73d9f7 exists (2026-10-18T03:54:49Z, "fix: restore grok-to-chatgpt.md and append GORDUM for 1a14d24a02e23460"). Failing run 39095256309 was on cb9f86a9 (03:54:32Z).
- c546b9ca -> c546b9cabd2439c6be9a13c9880f70a5e6a02b82 exists (2026-10-18T05:50:25Z, "Fix: restore full grok-to-chatgpt.md ...").
- archive-heal run 39101934643: completed / success, head_sha c546b9ca, main, 05:50:28Z-05:51:10Z.
- Failing run 39101909754 was on c4b6321e (05:50:04Z). Run 39101598018 not individually fetched.
- .github/workflows/codeql.yml (main, blob f53eed67): push + pull_request both have a `paths:` filter (py/js/ts/yml/... ),
  job uses `strategy.matrix.language: [python, javascript-typescript]`, steps are only checkout@v7, codeql init@v4,
  codeql analyze@v4 - no pip/apt step to cache. Claim confirmed.

## Exact changes (only these 4 records; everything else untouched)

### 1. CI-39095256309
```
-      "status": "open",
+      "status": "done",
-      "updated_at": "2026-10-18T03:56:29+00:00",
+      "updated_at": "2026-10-18T06:45:00+00:00",
   notes: keep existing entry, append:
+        "2026-10-18T06:45:00+00:00 chatgpt: done; archive-heal failure on cb9f86a9 fixed by abde94acd1699560fd053c68a478b6750c73d9f7 (grok-to-chatgpt.md restored + GORDUM appended); commit verified via GitHub get_commit."
   after the closing `]` of notes add:
+      "claimed_at": "2026-10-18T06:45:00+00:00",
+      "done_sha": "abde94acd1699560fd053c68a478b6750c73d9f7",
+      "done_at": "2026-10-18T06:45:00+00:00"
```

### 2. CI-39101598018
```
-      "status": "open",
+      "status": "done",
-      "updated_at": "2026-10-18T05:47:02+00:00",
+      "updated_at": "2026-10-18T06:45:00+00:00",
   notes: append:
+        "2026-10-18T06:45:00+00:00 chatgpt: done; fixed by c546b9cabd2439c6be9a13c9880f70a5e6a02b82 (full grok-to-chatgpt.md restored); evidence: archive-heal 39101934643 green (success @c546b9ca)."
+      "claimed_at": "2026-10-18T06:45:00+00:00",
+      "done_sha": "c546b9cabd2439c6be9a13c9880f70a5e6a02b82",
+      "done_at": "2026-10-18T06:45:00+00:00"
```

### 3. CI-39101909754
```
-      "status": "open",
+      "status": "done",
-      "updated_at": "2026-10-18T05:51:53+00:00",
+      "updated_at": "2026-10-18T06:45:00+00:00",
   notes: append:
+        "2026-10-18T06:45:00+00:00 chatgpt: done; failure on c4b6321e fixed by c546b9cabd2439c6be9a13c9880f70a5e6a02b82; evidence: archive-heal 39101934643 green (success @c546b9ca)."
+      "claimed_at": "2026-10-18T06:45:00+00:00",
+      "done_sha": "c546b9cabd2439c6be9a13c9880f70a5e6a02b82",
+      "done_at": "2026-10-18T06:45:00+00:00"
```

### 4. HO-IMP-20261018-slow-codeql-code-scanning (not applicable -> `done`, no done_sha)
```
-      "status": "open",
+      "status": "done",
-      "updated_at": "2026-10-18T05:49:12+00:00",
+      "updated_at": "2026-10-18T06:45:00+00:00",
   notes: append:
+        "2026-10-18T06:45:00+00:00 chatgpt: not applicable - codeql.yml already uses paths filter and matrix; no pip/apt step (main 8fc7894e: push/pull_request paths filters, matrix [python, javascript-typescript], only checkout + codeql init/analyze). Closed as done like 57c9e355."
+      "done_at": "2026-10-18T06:45:00+00:00"
```
(If a `done_sha` is required by tooling, use main 8fc7894e9cecb02fb4ae2554a6f682dcf794b7e7 as the inspected state, as 57c9e355 did with 8f792ac9.)

## Apply + validate (Grok, on the box)

Load with `json.load`, edit only these 4 dicts (append keys so order matches above), dump with
`json.dumps(data, ensure_ascii=False, indent=2) + "\n"`, then `git diff --stat` must show only state/handoffs.json with
changes inside these 4 records, and `python3 -m json.tool state/handoffs.json >/dev/null` must pass.
Note: research-learner/ci-bekci bots append to this file often; rebase right before applying.

constraints: PayoutLens and grok-chatgpt-masa untouched. No secrets. No PR, no merge.
