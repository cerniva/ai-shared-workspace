# GitHub Actions OIDC immutable claims — CORE-05 feeder

- source_id: src_core05_github_oidc_immutable_20260929
- canonical: https://docs.github.com/en/actions/reference/security/oidc
- evidence_tier: official
- verified_at: 2026-09-29T04:03:00+03:00
- category: github-actions-identity-security
- status: verified-new-delta

## Verified delta
GitHub's current OIDC reference states that repositories created after 2026-07-15 use an immutable default `sub` format containing owner ID and repository ID. Older repositories keep the prior name-based format unless they opt in; repository rename/transfer after that date also moves to the immutable format. OIDC requires `id-token: write` only to request the JWT; it does not itself grant resource write access.

## Gap this can close
CORE-05 currently has multiple external/provider integrations and long-lived secret/credential gates. For any future cloud/service integration that supports GitHub OIDC, short-lived federated credentials can reduce long-lived secret exposure. If an OIDC trust policy is added, CORE-05 must first determine which subject format this repository actually emits and bind the provider trust policy to the exact repo/workflow/environment claims rather than assuming the older name-only subject.

## Decision value
Candidate for CORE-05 execution queue: inventory only integrations that actually support GitHub OIDC; for each, compare current long-lived-secret auth with short-lived OIDC. Do not migrate blindly. Before any migration, inspect current workflow permissions and provider trust conditions, then test in a non-destructive workflow. Prefer immutable subject claims where supported and appropriate.

## Confidence / limits
High confidence in GitHub behavior because the source is current official documentation. This note does not prove this repository's creation date, current OIDC subject format, or that any existing third-party provider supports GitHub OIDC. Those facts require live inspection before implementation.

PayoutLens untouched. No fix applied by this feeder.
