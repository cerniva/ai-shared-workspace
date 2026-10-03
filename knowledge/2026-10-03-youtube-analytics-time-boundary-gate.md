# YouTube Analytics Pacific-Time Boundary Gate

- learning_id: learn_youtube_analytics_pacific_time_boundary_gate_20261003
- source_id: src_google_youtube_analytics_dimensions_time_20261003
- topic: youtube_analytics_time_semantics
- source_type: official_primary_documentation
- canonical_url: https://developers.google.com/youtube/analytics/dimensions
- finding: YouTube Analytics API day/month report dates are defined on Pacific-time calendar boundaries, not the operator's local timezone. A day begins 00:00 Pacific and ends 23:59 Pacific; DST transitions can therefore produce 23- or 25-hour reporting days. The API also returns only through the last day for which all requested metrics are available. Local Istanbul calendar-day comparisons must not be treated as equivalent to API day rows without timezone alignment.
- evidence_confidence_limit: High confidence for API time semantics from Google primary documentation. This does not prove YouTube Studio UI uses identical boundaries for every card/report, and it does not prove owned-channel data availability or latency for any specific metric.
- affected_plans: Video/Shopify; Sistem Geliştirmeleri
- old_approach: Compare daily YouTube Analytics rows directly against local Istanbul dates/timestamps.
- learned_rule: TIME_BOUNDARY_GATE — preserve API day/month semantics in Pacific time; when comparing with Istanbul-local events/uploads, convert timestamps explicitly and label the reporting boundary. Do not attribute a day-over-day change to a local-calendar event unless the event window overlaps the API reporting day. Keep latency/completeness gate separate.
- applied_test_next_measurement: For a mature owned-channel Short, compare upload/event timestamp in Europe/Istanbul against the corresponding Pacific reporting day before calculating day-over-day engagedViews/watch-time/retention deltas.
- discovered_at: 2026-10-03T16:28:00+03:00
- last_verified: 2026-10-03
- access_status: web_only
- failure_history: No authenticated owned-channel Analytics response was available in this cycle; target-plan runtime consumption remains unverified.
- fallback: If exact event timestamp or authenticated daily Analytics is unavailable, avoid local-day causal claims; use explicitly labeled aggregate/mature-window metrics instead.
- provenance: Google YouTube Analytics dimensions documentation; YouTube for Artists official analytics guidance was also reviewed for practical analytics context, but it did not establish the API timezone rule and is not the critical evidence.
- first_added_cycle: 2026-10-03-cycle-11
- last_used_cycle: 2026-10-03-cycle-11
- use_count: 1
- status: active
- persistence_status: pending_read_back
- bridge_status: bridge_failure_target_plan_consumption_unverified

## Decision value

This prevents false daily comparisons when the operator is in Turkey: an Istanbul calendar day and a YouTube Analytics API `day` row do not share the same midnight boundary. It also prevents DST-length days from being assumed to contain exactly 24 hours.
