# RPT-20261004-1222-grok-retention-shopify

## RPT-20261004-1222-grok-seen

- from: grok
- project: video-shopify
- task: seen ack for new retention and Shopify validation mail
- status: seen
- completed: GÖRDÜM sent before the rule commit.
- evidence: Gmail send accepted, reply message 1a1063946b16833f, thread 1a10638da0c23f72, rfc reply_to HWsGGr2rRcmrTHrBnHs5Xg@geopod-ismtpd-12. Bounce search returned no DSN. ChatGPT chat delivery not proven.
- decision_or_conflict: seen is not completion.
- next_action: persist only rules that the public pages support.

## RPT-20261004-1230-grok-retention-shopify-gates

- from: grok
- project: video-shopify
- task: new retention and Shopify validation rules
- status: in_progress
- completed: five gates encoded and unit-tested locally. Origin commit is the persistence proof.
- evidence: Mail truncated. Sources listed in knowledge/2026-10-04-retention-shopify-validation-gates.md. Local unittest 5/5 OK.
- decision_or_conflict: CONSENSUS with official AVD loop exclusion, single-video retention query, null available, and automated date eligibility. Market-rate rule is from the Shopify blog, not a store read.
- knowledge_to_keep: Do not treat APV over 100 as loop proof. Do not coerce untracked available null to 0. Do not sum matching shipping rates.
- sources: https://developers.google.com/youtube/analytics/metrics ; https://developers.google.com/youtube/analytics/sample-requests ; https://shopify.dev/docs/api/admin-rest/latest/resources/inventorylevel ; https://help.shopify.com/en/manual/fulfillment/setup/delivery-expectations/automated-delivery-dates ; https://www.shopify.com/blog/fulfillment-on-shopify-2026
- next_action: same mail not processed again. No FURKAN step unless a store admin read is wanted later.
