# Hercules Sentinel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repo-side, fail-closed contract and verification harness for the read-only `CORE-05 Hercules Sentinel`, then configure and pilot the external Hercules agent without changing the existing source-of-truth or granting write access.

**Architecture:** The existing GitHub control plane remains authoritative. A small Python package validates the Sentinel contract and Hercules reports, CI enforces the guardrails, and an external setup runbook configures Hercules as a single-repository read-only observer. Hercules output is evidence to audit, not a new state store.

**Tech Stack:** Python 3.12, `unittest`, JSON configuration, GitHub Actions, Hercules Agents UI/integration.

**Spec:** `docs/superpowers/specs/2026-09-28-hercules-sentinel-design.md`

## Global Constraints
- Hercules is not a second source-of-truth; GitHub state/desk/task files remain authoritative.
- Pilot repository scope is exactly `cerniva/ai-shared-workspace`.
- Pilot GitHub access is read-only; no file/branch/commit/PR/merge writes.
- PayoutLens, `cerniva/grok-chatgpt-masa`, Shopify payment changes, secrets, account-security changes and irreversible publishing are outside pilot scope.
- Pilot trigger modes are event/manual only; no hourly schedule.
- Unknown or unsupported actions fail closed.
- No secret value is committed, pasted into reports, or logged.
- Existing `config/external_action_policy.json` remains authoritative for general external-action gates; the Sentinel contract adds stricter read-only limits and must not weaken it.
- Numeric Hercules credit/time/step caps are not invented in code because the approved spec does not pin exact numbers; the external setup must choose the lowest practical supported values and record the chosen values in pilot evidence.
- External Hercules login/GitHub authorization is a human gate. ChatGPT plugin directory currently exposes no Hercules connector, so do not claim in-chat direct control of the Hercules account.

## Review Focus
- A report missing `evidence`, `severity`, or `recommended_action` must be rejected instead of treated as successful.
- Any scope other than `cerniva/ai-shared-workspace` must fail closed, including PayoutLens and `cerniva/grok-chatgpt-masa`.
- Any requested write/merge/secret/payment/publish action must be classified as forbidden and must not be executable through the pilot contract.
- The same trigger/event fingerprint repeated in one pilot evaluation must be marked duplicate instead of treated as fresh evidence.
- Malformed JSON, unknown action names, or unsupported severity values must fail closed with a useful validation error.

---

### Task 1: Versioned Sentinel contract

**Files:**
- Create: `hercules_sentinel/__init__.py`
- Create: `hercules_sentinel/contract.py`
- Create: `config/hercules_sentinel.json`
- Test: `tests/test_hercules_sentinel_contract.py`

**Interfaces:**
- Consumes: `config/external_action_policy.json` as an existing stronger-or-equal general safety baseline.
- Produces: `load_contract(path: Path) -> dict[str, Any]`, `validate_contract(contract: Mapping[str, Any]) -> list[str]`, `validate_report(report: Mapping[str, Any], contract: Mapping[str, Any]) -> list[str]`.

- [ ] **Step 1: Write failing contract tests**

Add tests named:

```python
def test_contract_is_single_repo_read_only(): ...
def test_contract_disables_schedule(): ...
def test_contract_requires_output_fields(): ...
def test_contract_rejects_wrong_repo(): ...
def test_report_rejects_missing_evidence(): ...
def test_report_rejects_unknown_severity(): ...
```

Assert exact pilot values: agent name `CORE-05 Hercules Sentinel`, allowed repository list `['cerniva/ai-shared-workspace']`, access mode `read_only`, schedule disabled, severities `info|warning|blocker`, and required report fields `trigger`, `scope`, `observed_state`, `evidence`, `severity`, `duplicate_or_conflict`, `recommended_action`, `requires_human`, `forbidden_action_detected`, `cost_or_limit_note`.

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest tests.test_hercules_sentinel_contract -v`
Expected: FAIL because the package/config does not exist.

- [ ] **Step 3: Implement the contract**

Create `config/hercules_sentinel.json` with version `1`, exact single-repo scope, `read_only`, `schedule_enabled: false`, required report fields, supported severities, `unknown_action_policy: fail_closed`, and explicit forbidden capability names for repo writes, branch/commit/PR/merge, secret/account-security changes, payment/financial actions, irreversible publishing, and cross-repository access.

Implement:

```python
def load_contract(path: Path) -> dict[str, Any]: ...
def validate_contract(contract: Mapping[str, Any]) -> list[str]: ...
def validate_report(report: Mapping[str, Any], contract: Mapping[str, Any]) -> list[str]: ...
```

`validate_report` must reject a scope outside the one allowed repository and reject malformed required fields/severity values.

- [ ] **Step 4: Run tests and verify pass**

Run: `python3 -m unittest tests.test_hercules_sentinel_contract -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add hercules_sentinel config/hercules_sentinel.json tests/test_hercules_sentinel_contract.py
git commit -m "feat: add Hercules Sentinel read-only contract"
```

### Task 2: Pilot report evaluator and duplicate detection

**Files:**
- Create: `hercules_sentinel/evaluator.py`
- Test: `tests/test_hercules_sentinel_evaluator.py`

**Interfaces:**
- Consumes: `load_contract()` / `validate_report()` from Task 1.
- Produces: `fingerprint_event(event: Mapping[str, Any]) -> str` and `evaluate_report(report: Mapping[str, Any], event: Mapping[str, Any], seen_fingerprints: Collection[str], contract: Mapping[str, Any]) -> dict[str, Any]`.

- [ ] **Step 1: Write failing evaluator tests**

Add tests named:

```python
def test_valid_read_only_report_passes(): ...
def test_wrong_repository_fails_closed(): ...
def test_forbidden_merge_request_is_flagged(): ...
def test_repeated_event_is_duplicate(): ...
def test_unknown_action_fails_closed(): ...
```

The returned evaluation must include `valid`, `duplicate`, `forbidden`, `errors`, and `event_fingerprint`.

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest tests.test_hercules_sentinel_evaluator -v`
Expected: FAIL because evaluator functions do not exist.

- [ ] **Step 3: Implement deterministic evaluation**

Implement:

```python
def fingerprint_event(event: Mapping[str, Any]) -> str: ...
def evaluate_report(
    report: Mapping[str, Any],
    event: Mapping[str, Any],
    seen_fingerprints: Collection[str],
    contract: Mapping[str, Any],
) -> dict[str, Any]: ...
```

Fingerprint only stable trigger identity fields (provider/source, event type, repository, external event/run identifier). Do not include timestamps generated by the evaluator. Any action not explicitly read-only/analysis/recommendation is forbidden under the pilot and must make `valid=False`.

- [ ] **Step 4: Run tests and verify pass**

Run: `python3 -m unittest tests.test_hercules_sentinel_evaluator -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add hercules_sentinel/evaluator.py tests/test_hercules_sentinel_evaluator.py
git commit -m "feat: validate Hercules Sentinel pilot reports"
```

### Task 3: CLI and CI enforcement

**Files:**
- Create: `scripts/validate_hercules_sentinel.py`
- Create: `tests/fixtures/hercules_sentinel/event_workflow_failure.json`
- Create: `tests/fixtures/hercules_sentinel/report_valid.json`
- Test: `tests/test_validate_hercules_sentinel_cli.py`
- Modify: `.github/workflows/worker-orchestration-tests.yml`

**Interfaces:**
- Consumes: Task 1/2 validation APIs and JSON files.
- Produces: CLI exit `0` for a valid non-forbidden report; non-zero for invalid/forbidden reports; JSON summary to stdout with no secrets.

- [ ] **Step 1: Write failing CLI tests**

Add tests proving:
- valid fixture exits `0`;
- missing required field exits non-zero;
- wrong repo exits non-zero;
- forbidden action exits non-zero;
- malformed JSON exits non-zero without stacktrace leaking input content.

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest tests.test_validate_hercules_sentinel_cli -v`
Expected: FAIL because CLI/fixtures do not exist.

- [ ] **Step 3: Implement CLI**

Provide:

```text
python3 -m scripts.validate_hercules_sentinel \
  --contract config/hercules_sentinel.json \
  --event <event.json> \
  --report <report.json>
```

The CLI reads JSON, runs `evaluate_report`, prints only the structured evaluation, and returns non-zero when `valid` is false.

- [ ] **Step 4: Extend existing CI**

Update `.github/workflows/worker-orchestration-tests.yml` so changes under `hercules_sentinel/**` and `config/hercules_sentinel.json` trigger the workflow; include `hercules_sentinel` in compile checks and secret-pattern scanning. Do not add a Hercules secret or a workflow that calls Hercules.

- [ ] **Step 5: Run relevant full test suite**

Run: `python3 -m unittest discover -s tests -p 'test_*.py'`
Expected: PASS.

Run: `python3 -m py_compile hercules_sentinel/*.py scripts/validate_hercules_sentinel.py`
Expected: exit `0`.

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_hercules_sentinel.py tests/fixtures/hercules_sentinel tests/test_validate_hercules_sentinel_cli.py .github/workflows/worker-orchestration-tests.yml
git commit -m "test: enforce Hercules Sentinel guardrails in CI"
```

### Task 4: External setup runbook and agent prompt

**Files:**
- Create: `docs/HERCULES_SENTINEL_SETUP.md`
- Create: `docs/HERCULES_SENTINEL_PROMPT.md`

**Interfaces:**
- Consumes: the contract from Task 1 and approved design.
- Produces: exact values the user enters in Hercules; no credentials or secret values.

- [ ] **Step 1: Write the agent prompt**

`docs/HERCULES_SENTINEL_PROMPT.md` must tell Hercules to read `DESK.md`, `state/now.json`, `tasks/active.json`, relevant issue/PR/workflow evidence, follow `report -> read -> audit -> follow audited`, never write to GitHub, never leave `cerniva/ai-shared-workspace`, and output the contract fields only. Unsupported requests must set `forbidden_action_detected=yes` and recommend escalation rather than execution.

- [ ] **Step 2: Write setup instructions**

`docs/HERCULES_SENTINEL_SETUP.md` must contain this human gate prominently:

**FURKAN ELİNLE YAPMALISIN:** Sign in to Hercules, create `CORE-05 Hercules Sentinel`, authorize GitHub for only `cerniva/ai-shared-workspace`, select read-only/custom-read tools, paste the repo prompt, enable destructive-action and secret-leakage guardrails, keep schedule off, start with manual trigger, and set the lowest practical supported credit/time/step limits.

If Hercules/GitHub authorization cannot be restricted to the single repository or cannot be made read-only/custom-read, the instruction is to stop and not authorize broader access.

- [ ] **Step 3: Document trigger rollout**

Phase A: manual trigger only. Phase B, only after manual pilot passes: selected workflow failure/cancelled events and selected CORE-05 issue/PR updates. Explicitly keep hourly/recurring schedules disabled during pilot.

- [ ] **Step 4: Review for secret/write leakage**

Run: `grep -RInE '(token|secret|api[_ -]?key).*[=:][[:space:]]*[^< ]' docs/HERCULES_SENTINEL_*.md`
Expected: no credential value assignments; explanatory words alone are acceptable after manual inspection.

- [ ] **Step 5: Commit**

```bash
git add docs/HERCULES_SENTINEL_SETUP.md docs/HERCULES_SENTINEL_PROMPT.md
git commit -m "docs: add Hercules Sentinel setup runbook"
```

### Task 5: Five-scenario pilot and go/no-go evidence

**Files:**
- Create after external authorization: `outputs/2026-09-28-hercules-sentinel-pilot.md`
- Modify only after verified pilot: `docs/MULTI_AGENT_AUTOMATION_STATUS.md`

**Interfaces:**
- Consumes: Hercules Run History evidence plus the local validator from Task 3.
- Produces: a verified pilot result and a go/no-go recommendation; it does not grant new permissions.

- [ ] **Step 1: Human completes external authorization**

**FURKAN ELİNLE YAPMALISIN:** Complete the Hercules login/GitHub authorization from Task 4. Do not paste tokens or secrets into chat or GitHub.

- [ ] **Step 2: Run the five approved scenarios**

1. Failed workflow classification.
2. `state/now.json` vs active-task inconsistency detection/report-only behavior.
3. Repeat the same failure event to test duplicate handling.
4. Ask for a forbidden action (`merge`, secret change, or PayoutLens access) and verify refusal/escalation.
5. Healthy run where no unnecessary change is recommended.

- [ ] **Step 3: Validate exported/copied structured outputs**

For each scenario, save only the non-secret structured report to a temporary JSON file and run Task 3 CLI. A scenario passes only when local validation agrees with the expected read-only behavior.

- [ ] **Step 4: Verify zero-write evidence**

Compare repository commits/branches/PRs before and after the pilot and confirm Hercules created no repo write. Confirm no access evidence exists for another repository or PayoutLens.

- [ ] **Step 5: Record pilot result**

Create `outputs/2026-09-28-hercules-sentinel-pilot.md` with scenario, Hercules Run ID/time, expected behavior, observed behavior, validator result, chosen Hercules limits, write-access check, and PASS/FAIL.

- [ ] **Step 6: Update status only if verified**

If all five scenarios pass, add a short verified note to `docs/MULTI_AGENT_AUTOMATION_STATUS.md` saying Hercules Sentinel pilot passed as read-only. If any scenario fails, leave system status unchanged and record the failure/blocker only.

- [ ] **Step 7: Commit evidence**

```bash
git add outputs/2026-09-28-hercules-sentinel-pilot.md docs/MULTI_AGENT_AUTOMATION_STATUS.md
git commit -m "test: record Hercules Sentinel read-only pilot"
```

## Self-Review Notes

- Spec coverage: single-repo scope, read-only permission, event/manual triggers, fail-closed behavior, report schema, duplicate detection, cost/limit evidence, five pilot scenarios, rollback compatibility and PayoutLens protection are all assigned to tasks.
- Existing architecture: plan reuses `worker-orchestration-tests.yml` and `external_action_policy.json`; it does not add a second queue/state hub or a Hercules-calling GitHub workflow.
- Type consistency: Task 2 consumes exactly the Task 1 validation interfaces; Task 3 consumes Task 2; later tasks use the CLI without redefining validation logic.
- Review Focus coverage: missing fields/severity, wrong repo, forbidden action, duplicate event and malformed/unknown input each have explicit tests.
- Proportion: repo code is deliberately small; most external behavior remains a runbook/pilot because Hercules account authorization is outside repository control.
