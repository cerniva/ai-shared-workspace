# Archive restored-marker guard audit — 2026-10-13 20:32 TRT

Base main commit: 5d46398a4d1a3769f57c89bd2590a2db9e8d3359
Branch: chatgpt/archive-restored-sentinel-regression-20261013

Observed: scripts/archive_heal.py BODY_SENTINEL detects FULL_CONTENT_* and truncated-response sentinels but not a standalone RESTORED_FROM_PREVIOUS_COMMIT_* line. Main grok archive currently has no matching active standalone marker in the inspected file; historical reports describe prior removal. Do not modify protected archives without a history-preserving comparison.

Suggested change: recognize standalone RESTORED_FROM_PREVIOUS_COMMIT_[A-Z0-9_-]+ in BODY_SENTINEL, keeping prefixed evidence/decision lines intact. Add positive and negative unittest cases to tests/test_archive_heal_sentinels.py.

Isolated regex checks: 2 unittest methods passed locally (4 positive and 4 negative examples). This is not the full repository suite. GitHub script update was blocked by safety checks; no code fix or CI is claimed.

PR #131: open draft, old head 3fa345571ec7dc4e3f28070e8e6414b764894d69; clean alternative PR #183 already merged. PR #127: open draft, head 83382dcc75d90ef83abc50b3832e9ce53df9a5ac; old successful CI does not prove compatibility with current main.

Handoff ledger: valid JSON, 23 items, five open >45m (HO-20261009-08, CI-38337554641, CI-38337738841, HO-IMP-20261013-slow-research-learner, CI-38372167749). HO-03/HO-13 completed according to prior reconciliation; no new task opened.

Owner for archive regression: Grok or authorized coding agent. Next: apply the tiny code/test change on a PR branch, run python3 -m unittest discover -s tests -p 'test_*.py', verify PR CI, and read back main after reviewed merge. Owner for HO-08 OAuth: auditor/user authorization required; no OAuth change.

Protected archives, workflows, secrets, publishing, payments and PayoutLens were not modified.
