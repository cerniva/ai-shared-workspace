# PR review options from user-provided Gemini screenshots

Status: user_reported, not externally verified. This is a proposal, not a deployed bot.

Reuse existing GitHub Actions, CodeQL, tests and provider-health checks before adding another reviewer. GitHub Models and Gemini were usable in the latest health record; Groq, OpenRouter and Cerebras had no configured keys.

Proposed PR review: run deterministic tests first; then optionally request a read-only model review within confirmed free quotas. Include file, line, severity and evidence. Never auto-merge or deploy based solely on model output. Deduplicate by commit SHA, limit retries, and report model_unavailable when no eligible provider works. Keep secrets unavailable to untrusted PR code. External GitHub Apps require separate approval. Free pricing and quotas must be verified before use. PayoutLens excluded.

Acceptance: existing workflow overlap audited, least privileges checked, repeat-run tests passed, CI evidenced, and no changes to main without review.
