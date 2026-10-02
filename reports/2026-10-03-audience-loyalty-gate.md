# 2026-10-03 audience loyalty gate

- Timestamp: 2026-10-03T02:35:00+03:00
- Status: CONTINUE
- Trigger: Gmail from noreply@tm.openai.com, subject [Task Update] Bilgi Kütüphanesi: Audience loyalty gate added to knowledge library, message_id=1a0fef049e69bc32, thread_id=1a0fef049e69bc32, date Fri, 02 Oct 2026 23:25:54 +0000, rfc_message_id=<nv30kt6jQcmq0TwXQle-4g@geopod-ismtpd-99>. Body is a truncated notification, not the full rule.
- GÖRDÜM: gmail_send_message accepted in the same thread, sent_message_id=1a0fef0a9d025af6. Bounce not observed. Sender is noreply@tm.openai.com, so ChatGPT chat delivery is not claimed.

## Read-back
- main HEAD at read: 9003f3dfb4f4e42f61881ebe3da580ea3fcd2e29
- commit message: knowledge: add YouTube audience loyalty gate
- file: knowledge/2026-10-03-youtube-audience-loyalty-gate.md blob ea987f2e19bda1eb2253a2e893f44c13d2c2697a (+23)
- learning_ledger.json blob dd0f5c0e81207e76e5535adbbc4d1345fdf9ff24 had no loyalty/audience row (18 learnings)
- source_catalog.json had answer/9314415 (src_59f52b1f650983e4) but not answer/10246996
- markdown source_id youtube-help-audience-watch-behavior-2026 is not a machine source_id

## Official check 2026-10-03
- https://support.google.com/youtube/answer/10246996
- New: first time in the selected period; private browser, deleted watch history, or no watch for over a year count as new.
- Casual: at least once per month for 1-5 months in the past year.
- Regular: at least once per month for more than 6 months in the past year.
- Regular share can be below 1%, common for newer channels, trending videos, and channels that mostly post Shorts.
- Audience segments do not affect reach or monetization.
- Viewer totals are available for last 7, 28, and 90 days; data updates every 1-2 days.
- https://support.google.com/youtube/answer/9314415 returning viewers are a coarser new/returning split, not casual/regular.

## Decision
CONSENSUS on AUDIENCE_LOYALTY_GATE with nuance. Do not penalize a new or Shorts-heavy channel for a low regular share. Do not treat mix as proof one Short caused loyalty. Segments are not a reach or monetization penalty. No authorized Audience read; loyalty state for the owned channel stays unknown.

## Local proof before push
- Planned machine source src_d8c0211c4b948b1f for https://support.google.com/youtube/answer/10246996
- Planned learning learn_adb554bb622bcfb4
- unittest tests.test_knowledge_bridge and tests.test_learning_bridge: 12 OK after local catalog/ledger append
- PayoutLens untouched. No secrets. No publish, login, or delete.
