# YouTube Shorts clickable-link routing

Status: active
Learning ID: learn_youtube_shorts_clickable_links_20261002
Affected plans: Video/Shopify, Bilgi Kütüphanesi
Checked: 2026-10-02

## Verified finding
Official YouTube Help states that URLs placed in Shorts comments and Shorts descriptions are non-clickable. A Shorts `Related video` link is clickable in the Shorts player; adding a related video requires advanced feature access, and the selected video must be public or unlisted and comply with Community Guidelines.

## Decision value
Do not design a Shorts conversion/traffic CTA that depends on a raw URL in the Short description or comments being clickable. When the desired destination is another item of content on the same YouTube channel and advanced-feature access is actually available, prefer the native Related video path. For external destinations, use only a separately verified clickable surface that is appropriate to the goal; do not infer clickability from plain text URLs.

## Evidence
- https://support.google.com/youtube/answer/13748639
- https://support.google.com/youtube/answer/14075157

## Confidence / limits
High confidence for YouTube-native clickability behavior because both claims come from current official YouTube Help. This record does not assert that this channel currently has advanced-feature access; that must be verified before use.

## Test / next measurement
On the next suitable Short, Video/Shopify should read this Learning ID before CTA design. If Related video is chosen, verify advanced-feature access and remote saved state in YouTube Studio, then compare downstream viewing behavior using available channel analytics. Do not claim conversion lift without owned analytics.

## Provenance
Primary official documentation; no creator-opinion dependency. No secrets or PII stored.
