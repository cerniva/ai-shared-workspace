# Archive duplicate-ID guard — 2026-10-12 12:30 TRT

Base main SHA: da75e7f885fe2e0bbfc140c92c0d8229e62bd500
Branch: chatgpt/archive-duplicate-id-guard-20261012-1230
Code commit: fff63ac6acf67319923852cd3b0cc7b6c9fa5166
File: scripts/archive_heal.py

Read-only archive checks at base: 319 distinct message IDs out of 319 entries; 156 distinct report IDs out of 156 entries. No known isolated corruption markers.
New check: fail closed before archive writes when any message or report ID is duplicated.
Tests: repository suite not run. Attempts to add regression tests and create a draft PR were blocked by safety checks. Do not merge without tests and review.
PR #131 open draft; PR #127 open draft. HO-03 and HO-13 done; HO-08 open to auditor (OAuth permission blocker).
Protected archives, workflow, secrets and PayoutLens were not modified.

## Nöbet follow-up 2026-10-12 13:01 TRT
Grok nöbet: `assert_unique_record_ids` + `tests/test_archive_unique_record_ids.py` main'e alınacak (verify-before-green). Live archives 0 duplicate (319/156 unique). PayoutLens untouched.
