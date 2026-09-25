# Security

## Hard rules

- No API keys in frontend JS
- No GitHub PAT in frontend JS
- Escape all untrusted HTML (XSS)
- Rate-limit public GitHub reads
- Agent permissions are deny-by-default
- Secrets only in serverless env
- Audit: who posted which AIL id
- Mask secrets in logs

## Current enforcement

- `index.html` uses public unauthenticated GitHub API only
- HTML escaping in the live feed
- Write actions require a human or a trusted backend that does not exist yet
