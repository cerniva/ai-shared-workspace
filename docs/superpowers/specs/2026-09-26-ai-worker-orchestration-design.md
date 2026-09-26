# AI Worker Orchestration Design

## Goal
Make ChatGPT, Grok and Gemini behave as one coordinated system without pretending that GitHub itself wakes external models. ChatGPT remains the orchestrator; Grok and Gemini are evidence-producing workers.

## Scope
First release adds a durable task queue, structured worker results, ChatGPT review state, retry/failure semantics and secret-safe provider adapters. It does not add autonomous spending, unrestricted external messaging, or direct worker authority to change business strategy.

## Roles
- ChatGPT: orchestrator, prioritization, accept/reject/merge, execution and measurement.
- Grok: research, current-signal discovery, adversarial review and opportunity analysis.
- Gemini: Google/YouTube verification, independent source checking and second analysis.
- GitHub: durable shared state, queue, evidence and audit trail; not a scheduler by itself.

## State machine
A work item moves `queued -> claimed -> completed -> reviewed -> applied`.
Failure states are `retryable_failed`, `blocked` and `dead_letter`. A worker may write evidence/results but cannot mark its own result `reviewed` or `applied`.

## Work item contract
Each item has: id, project, objective, worker, priority, created_at, status, evidence_requirements, max_attempts, attempt_count and optional blocker. Claims record worker and timestamp. Results contain evidence, factual findings, hypotheses, recommendation, confidence and next_action.

## Review contract
ChatGPT records `accept`, `reject` or `merge`, rationale, accepted lesson(s), action and metric to watch. Only accepted reusable lessons enter `knowledge/lessons.md`.

## Scheduling
Provider workers are invoked only by an actual scheduler/runner. GitHub state changes alone never count as execution. A runner may be invoked on a conservative schedule or explicit queue event. Provider calls must be bounded by max attempts and configured budget/rate controls.

## Provider adapters
Provider-specific code is isolated behind a common worker interface. Grok requires xAI API credentials supplied only through a secret/environment mechanism. Gemini likewise uses a supported authenticated API path. Missing credentials produce `blocked`, never fake output.

## Reliability
Claims use a lease/timeout so abandoned jobs can be retried. Idempotency is by work-item id plus attempt. Duplicate completion is ignored. Retries are bounded; exhausted jobs enter dead-letter. One provider failure cannot stop other projects.

## Security and cost
Never commit API keys, tokens, passwords or personal credentials. No automatic purchases or subscription upgrades. Log provider/model, timestamps, token/cost data when available, but never secret values. Default to low-cost research and only escalate expensive calls when expected value justifies it.

## Revenue alignment
Every research job should connect to a business decision where practical. Preferred result chain: evidence -> lesson -> changed decision -> experiment/action -> metric -> revenue/lead/conversion outcome. PayoutLens remains primary until evidence changes priority.

## Success criteria
1. Queue schema validates valid/invalid transitions.
2. A mock Grok/Gemini worker can claim and complete a job without external credentials.
3. ChatGPT review is required before lessons/actions are marked applied.
4. Duplicate executions do not duplicate results.
5. Missing provider secrets fail safely as blocked.
6. Retry exhaustion reaches dead-letter.
7. Existing shared-state files remain readable and compatible.
