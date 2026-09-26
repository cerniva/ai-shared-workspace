# Shopify Admin API + YouTube Analytics API Setup

## Shopify Admin API

Worker connector: `scripts/connectors/shopify_client.py`

Required GitHub Secrets:
- `SHOPIFY_STORE`
- `SHOPIFY_CLIENT_ID`
- `SHOPIFY_CLIENT_SECRET`

Current Shopify platform note: new admin-created custom apps are no longer created from the store admin. Use Shopify Dev Dashboard for a new API-only app.

Recommended scopes for the first read-only version:
- `read_products`
- `read_orders`
- `read_inventory`

Flow:
1. Create an API-only app in Shopify Dev Dashboard.
2. Create/release a version with the read-only scopes above.
3. Install the app on the target store.
4. Copy Client ID and Client secret into GitHub Secrets.
5. Save store `*.myshopify.com` domain as `SHOPIFY_STORE`.
6. Worker uses Shopify client-credentials grant to request a short-lived Admin API token when needed.

If Shopify returns `shop_not_permitted`, the app/store are not in the same Shopify organization; use an OAuth/custom-distribution flow instead.

## YouTube Analytics API

Worker connector: `scripts/connectors/youtube_analytics_client.py`

Required GitHub Secrets:
- `YT_ANALYTICS_CLIENT_ID`
- `YT_ANALYTICS_CLIENT_SECRET`
- `YT_ANALYTICS_REFRESH_TOKEN`

Required scope for normal channel analytics:
- `https://www.googleapis.com/auth/yt-analytics.readonly`

Optional monetary scope (do not request unless needed):
- `https://www.googleapis.com/auth/yt-analytics-monetary.readonly`

Flow:
1. Enable YouTube Analytics API in Google Cloud.
2. Configure Google Auth Platform / OAuth consent.
3. Create a Web Application OAuth client.
4. Add `https://developers.google.com/oauthplayground` as an authorized redirect URI for the one-time setup.
5. Use Google OAuth 2.0 Playground with your own OAuth client credentials, server-side flow, Offline access.
6. Authorize `yt-analytics.readonly` with the Google account that owns the YouTube channel.
7. Exchange the code and copy the refresh token to GitHub Secret `YT_ANALYTICS_REFRESH_TOKEN`.
8. Save Client ID and Client secret as the other two GitHub Secrets.
9. Remove the OAuth Playground redirect URI later if it is no longer needed.

The connector supports:
- 28-day channel overview
- per-video audience retention using `elapsedVideoTimeRatio`, `audienceWatchRatio`, and `relativeRetentionPerformance`

## Inbox routing flags

Use these fields in `messages/inbox-gemini.md` when the worker should load private connector data:

```text
use_shopify: true
use_youtube_analytics: true
video_id: VIDEO_ID
```

Connector enrichment runs before the Gemini worker and appends only the requested data context.
