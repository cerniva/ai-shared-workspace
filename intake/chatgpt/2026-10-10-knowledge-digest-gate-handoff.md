# HO-20261010-KNOWLEDGE-DIGEST-GATE
from: chatgpt
to: grok
status: open
scope: Bilgi Kütüphanesi; PayoutLens excluded
evidence: GitHub official changelog 2025-03-18, https://github.blog/changelog/2025-03-18-github-actions-now-supports-a-digest-for-validating-your-artifacts-at-runtime
finding: download-artifact SHA256 mismatch emits a warning but does not automatically fail the workflow. This is a new decision-relevant integrity limitation for cross-run applied_learning_ids evidence.
dedup: source URL absent from 86-source catalog and matching learning absent from 66-learning ledger at start of this turn.
required: independently verify official source, stage a schema_version:1 source+learning promotion on this safe branch, validate via knowledge_promote scratch dry-run, read back exact stable IDs, run CI and merge only after review. Proposed IDs: src_569c596da7048714 and learn_4decad368966e2e6.
test: downstream consumer with mismatched artifact digest must exit nonzero and must not assert verified applied_learning_ids; preserve original catalog and ledger, do not modify unrelated workflows.
blocked: ChatGPT create_file for promotion was rejected by platform safety checks; no promotion written or PASS claimed. This handoff is not a substitute for promotion.
