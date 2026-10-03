# Meta Advisory Bridge

## Purpose
Use Meta AI as a real advisory/research opinion source without pretending it has a GitHub connector or repository write access.

## Truth model
- Meta consumer chat: advisory input only.
- GitHub: canonical state, code, tests and decision records.
- ChatGPT: orchestration/synthesis.
- A Meta opinion counts toward consensus only when its actual response is ingested with provenance and read back from the repository.
- Never infer a Meta response from a queued prompt or failed API call.

## Flow
1. Team creates a scoped prompt in `messages/inbox-meta.md` with a stable task/correlation id.
2. Prompt is sent to the real Meta surface when available.
3. Actual Meta response is ingested into `messages/paste-from-meta.md` or `messages/meta-to-chatgpt.md` with timestamp, task id and source=`meta-user-supplied`/verified connector provenance.
4. ChatGPT reads the response, compares it with other real AI opinions and repository evidence.
5. Important production/code decisions record options, disagreements, selected decision, evidence, test and rollback.
6. GitHub change is applied only through an authorized GitHub path and then tested/read back.

## Consensus gate
For important production/code/software decisions, prefer at least two genuinely independent available opinions. Unavailable providers do not count. A failed API, queued task, stale file, or simulated role never counts as a vote.

## Safety
No secrets, payment data or PII in messages. PayoutLens is excluded. User approval remains required for payment, publication, sensitive permission and irreversible actions.
