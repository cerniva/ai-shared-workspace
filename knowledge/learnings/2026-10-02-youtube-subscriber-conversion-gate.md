# Subscriber conversion gate

Date: 2026-10-02
Status: verified rule, no owned-channel numbers
Source: https://developers.google.com/youtube/analytics/metrics checked 2026-10-02

When a YouTube Analytics report uses the video dimension or a video filter, subscribersGained and subscribersLost include only subscribe and unsubscribe actions from that video's watch page. Channel reports also include the channel page and the home guide. A video-filtered net (`subscribersGained - subscribersLost`) must be labeled watch-page-attributed. It is not total channel subscriber change and not proof that the Short caused every new subscriber. Shorts-feed attribution is not claimed.

Gate: after analytics maturity, record subscribersGained, subscribersLost, net subscribers, engagedViews, and net subscribers per 1,000 engaged views when the denominator is positive. Do not score the Short on raw views alone. Do not invent numbers without a successful video-filtered read-back.

Repo gap at audit: lessons.md row existed on 4ba1549cf925faa984ba81583fd931559959662b. channel_overview already requests the two subscriber metrics and does not apply a video filter. Machine ledger row was absent before this audit.
