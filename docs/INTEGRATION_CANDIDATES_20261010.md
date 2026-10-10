# Isolated integration adapter candidates (2026-10-10)

Status: PLANNED / NOT CONNECTED. This module is not a PayoutLens fork. Do not touch cerniva/grok-chatgpt-masa, its secrets, deployments or data. Endeksa excluded by user.

| Tool | Purpose | Gate | Free fallback |
|---|---|---|---|
| Scite | scholarly citation checking | account/API entitlement + terms verified | Crossref / OpenAlex public research |
| Sentry | worker exception monitoring | existing project DSN and safe PII scrub smoke test | GitHub Actions logs |
| ClickUp | task visibility | account authorization, duplicate-task protection | existing GitHub tasks |
| Worp | Shorts research | official API/license + price and output test | existing free Shorts research workflow |
| AutoSEO | SEO insights | official API/license + evidence check | Search Console and manual metadata audit |
| Datadog | observability | region/account and pricing approval | Sentry / Actions logs |
| Hercules | app development alternative | official API + cost approval | existing GitHub code workflow |

No provider is installed by this document. No paid credits or user secrets are required for this planning-only change.

## Acceptance for each adapter
1. Confirm primary official docs, identity and permission scope; record cost and terms.
2. Implement optional, disabled-by-default adapter with bounded timeout, redaction and safe failure.
3. Test unauthorized/no-credential behavior without attempting login bypass.
4. Test real read-only call only after account authorization; record HTTP result, stdout/exit and read-back.
5. Integrate into existing four plans only after evidence proves it changes a decision or output. Record applied_learning_ids when applicable.
6. Keep PayoutLens excluded. Never treat successful CI without real action as a working integration.
