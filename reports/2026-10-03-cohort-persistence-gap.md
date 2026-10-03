# Cohort gate read-back and persistence gap

- when: 2026-10-03T10:24+03
- mail: [Task Update] Video ve Shopify Otomasyonu: Cohort gates verified and persistence gaps flagged
- gmail_message_id: 1a100a1683386ab0
- seen_commit: 9701a39083d9c3eb07e43866249d8bd9409f9d43
- mail_api_reply: 1a100a4d00141f0d
- rfc_in_reply_to: <BxQxNsnXS72noM33HdAzuA@geopod-ismtpd-57>
- bounce: not observed in send result. noreply sender; chat delivery not claimed.

## Verification on clone of 4c828b61715167e1323e70c3d68d413885e042d8

- COHORT_RFM_GATE row exists: learning_id learn_e877d8d8b1a1b290. Hash of domain+claim matches. Sources src_d04b5a72ae4029f9 and src_0c0576e57cb62ef8 present.
- Machine gate did not pass on that clone. learning_bridge validate raised unstable learning_id learn_a9a5c8d397ee3343. knowledge_bridge validate raised unstable source_id src_google_youtube_analytics_reports_query_20261003.
- Expected stable ids: learn_c26dcb3fda0b6b0c and src_1ee3fe3382f17f55. Claim and canonical URL were not changed.
- Wrong token COHORT_RFM_CONTEXT_GATE still fail-closed. No alias added.

## Repair

- Rewrote only those two ids in knowledge/learning_ledger.json and knowledge/source_catalog.json. Noted the prior ids in failure history.
- After rewrite: learning validate valid count 31; source validate count 51.
- COHORT_RFM_GATE persisted true, learning_id learn_e877d8d8b1a1b290, learning_count 31.
- YOUTUBE_ANALYTICS_DUAL_SCOPE_GATE persisted true, learning_id learn_c26dcb3fda0b6b0c, learning_count 31.
- unittest tests.test_learning_bridge tests.test_knowledge_bridge: 15 OK.
- Store admin not opened. No publish. PayoutLens untouched. No secrets.

## Decision

ACCEPT the mailed correction that COHORT_RFM_GATE is in the central ledger. DISAGREE that persistence was already green: the sibling dual-scope ids made the fail-closed gate fail. Ledger id rewrite is local until the ledger commit lands.
