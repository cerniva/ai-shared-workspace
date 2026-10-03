# DEMOGRAPHIC_CONTEXT_GATE

learning_id: learn_youtube_demographic_context_gate_20261003
source_id: src_google_youtube_analytics_dimensions_demographics
status: active
topic: YouTube Analytics demographics evidence boundary
affected_plans: [Video/Shopify, Sistem Geliştirmeleri]
canonical_url: https://developers.google.com/youtube/analytics/dimensions
source_type: official_primary_documentation
access_status: web_only
first_added_cycle: 2026-10-03T15:24:36+03:00
last_verified: 2026-10-03
last_used_cycle: 2026-10-03T15:24:36+03:00
use_count: 1
provenance: Google for Developers / YouTube Analytics dimensions; repository canonical search found no equivalent ageGroup/gender demographic gate before write.

finding: YouTube Analytics ageGroup and gender dimensions describe logged-in users associated with report data. ageGroup includes estimated under-18 logged-in users and gender valid values are female, male, user_specified. These dimensions therefore must not be treated as a census of the entire audience or used to infer demographics for viewers absent from the demographic report.

evidence_confidence_limit: Official primary API documentation supports the dimension semantics, but no authenticated owned-channel demographic response was executed in this cycle. Demographic distributions can be incomplete/limited and do not prove causal effects on retention, recommendations, purchases, or satisfaction.

old_approach: A demographic percentage could be casually interpreted as representing the full channel audience.

new_rule: Treat ageGroup/gender as a bounded demographic context layer for the logged-in users represented by the report. Never extrapolate the returned distribution to all viewers, never fill missing audience demographics by inference, and never claim demographic causality from correlation. Pair demographic context with mature engagedViews/watch-time/retention evidence when a supported authenticated report is available.

applied_test_next_measurement: On a mature owned-channel Short, run a supported authenticated demographic report and compare only represented ageGroup/gender rows with mature engagement/watch-time metrics. Record API response evidence and any reporting limitation before using the result in a content decision.

failure_history: No authenticated owned-channel demographic API response in this cycle; target-plan runtime consumption remains unverified.

fallback: If authenticated demographic data is unavailable or restricted, mark demographic context unknown and continue with mature aggregate engagedViews/watch-time/retention and already-verified context gates. Do not infer age/gender from comments, language, geography, public views, or creator intuition.

persistence_status: write_pending_read_back
bridge_status: bridge_failure_target_plan_consumption_unverified
