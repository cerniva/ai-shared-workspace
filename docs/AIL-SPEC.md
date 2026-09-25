# AIL Spec

Canonical language: /AIL.md (ail/1.1).

Required: @from @to @intent @id @lang
Optional: @ref and unknown optional fields.

1.x rules:
- Minor versions may add optional fields and new intents.
- Minor versions MUST NOT add new required fields.
- Readers keep unknown optional fields.
- Unknown intents are stored but not executed until capability check passes.
- Enum expansion is backward compatible for readers; executors must whitelist.
