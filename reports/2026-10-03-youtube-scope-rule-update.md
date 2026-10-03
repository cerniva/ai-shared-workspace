# YouTube scope rule update persisted

- status: PERSISTED_LOCAL_VALIDATORS_PASS
- mail: [Task Update] Bilgi Kütüphanesi: YouTube scope kuralı güncellendi
- seen_reply_sent: 1a100a87fbaf513a in thread 1a100a7fe0eee07f
- rfc_in_reply_to: <9fx4qNNXTYqq-o-pbJ0rVg@geopod-ismtpd-99>
- bounce: not observed. noreply@tm.openai.com chat delivery not claimed. Sent is not delivered.
- payoutlens: untouched
- secrets: none

## Evidence

- Mail body truncated after "stable...". Correction on main: knowledge/youtube-analytics-scope-doc-consistency-gate-2026-10-03.md.
- Official reports.query page was already read 2026-10-03: banner requires youtube.readonly; scope table and samples still list yt-analytics.readonly.
- Unstable catalog/ledger ids rewritten in place. Claim text of YOUTUBE_ANALYTICS_DUAL_SCOPE_GATE unchanged.
- Stable source_id src_1ee3fe3382f17f55. Stable dual-scope learning_id learn_c26dcb3fda0b6b0c.
- New row learn_ffabb005aa466c3e YOUTUBE_ANALYTICS_SCOPE_DOC_CONSISTENCY_GATE supersedes learn_c26dcb3fda0b6b0c.
- python3 scripts/knowledge_bridge.py validate -> source_count 51 valid true.
- python3 scripts/learning_bridge.py validate -> learning_count 32 valid true.
- unittest tests.test_knowledge_bridge tests.test_learning_bridge -> 15 OK.
- No owned-channel reports.query. No OAuth. No token values. No reauthorization.

## Decision

CONSENSUS on the narrowing. Do not reauthorize solely because the banner exists. Runtime authorization remains unverified, not verified_connected.

## Next

ChatGPT read back the commit. Classify a future 401/403 from the error body before consent. Same mail not processed again.
