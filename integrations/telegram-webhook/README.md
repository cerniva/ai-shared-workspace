# Telegram Worker rollout

## Dashboard-independent access

Cloudflare API access can run from GitHub Actions without the blocked browser
sign-in. This still requires a valid Cloudflare account token. Do not paste a
token, password or Telegram secret into chat, code, PR text or logs.

One-time repository configuration:
- Actions secret `CLOUDFLARE_API_TOKEN`: a Cloudflare API token with
  **Account / Workers Scripts / Read**, scoped to the intended account only.
- Actions variable `CLOUDFLARE_ACCOUNT_ID`: that account's 32-character ID.
- Actions variable `CLOUDFLARE_WORKER_NAME`: the exact existing Worker name.

Use GitHub Settings → Secrets and variables → Actions for these values.
A token already provisioned securely can be reused if its scope is appropriate.
If no token exists, an authorized Cloudflare account holder must provision one;
this workflow cannot bypass account authorization.

Once this workflow is available on the default branch, run
`telegram-webhook-test` on reviewed code with `cloudflare_preflight=true`.
PR runs execute tests only and never receive the Cloudflare token.
The optional job makes one GET request for the existing Worker's settings.
It does not follow redirects, retry rejected authentication, print API bodies,
deploy code, change bindings or contact Telegram. Output distinguishes read
access from deployment verification and reports only the presence/type of the
three expected Telegram bindings. A present binding does not prove its value
is valid. Missing/invalid configuration or failed access fails the job.

## Production remains gated

The workflow deliberately has no deploy step. Before any live change:
1. Inspect existing Worker code, settings, bindings and routes; record a
   recoverable version and current Telegram delivery configuration.
2. Preserve the existing Worker's functionality and bindings. Stage a version
   separately from production deployment; validate secret configuration and
   preview behavior with no real command sent to Telegram.
3. Keep the existing bot running. This Worker currently implements only
   /start, /yardim and /durum; switching it on would remove the polling bot's
   other commands. Resolve command parity and delivery ownership first.
4. Only after checks pass, perform a coordinated cutover with rollback.
   Do not delete pending Telegram updates.

For later staging/deployment, a separately scoped Workers Scripts Write token
will be necessary. Read access is intentionally sufficient for this first
check. Telegram secrets must be configured as Cloudflare encrypted secrets,
never plain variables or repository files.

Official references:
- https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/
- https://developers.cloudflare.com/workers/versions-and-deployments/
- https://developers.cloudflare.com/api/python/resources/workers/subresources/scripts/subresources/script_and_version_settings/methods/get/
