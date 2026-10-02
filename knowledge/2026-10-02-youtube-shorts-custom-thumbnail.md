# YouTube Shorts custom thumbnail — 2026-10-02

- learning_id: `learn_youtube_shorts_custom_thumbnail_20261002`
- topic: Shorts packaging / thumbnail capability
- source_type: official YouTube Help
- canonical_url: https://support.google.com/youtube/answer/72431
- finding: YouTube's current official help says verified accounts can upload a custom thumbnail for a Short from YouTube Studio on a computer. The recommended aspect ratio for uploaded Shorts thumbnails is 9:16. This is a newer capability and changes the prior assumption that Shorts packaging is limited to selecting an in-video frame.
- evidence_confidence_limit: Primary-source documentation verified 2026-10-02. Availability still depends on account verification and actual Studio UI/access; documentation alone does not prove the user's channel currently exposes the control.
- affected_plans: Video/Shopify; System Developments
- old_approach: Treat Shorts thumbnail control as frame-selection-only and design packaging solely around an in-video frame.
- learned_rule: `SHORTS_CUSTOM_THUMBNAIL_CAPABILITY_GATE` — For Shorts packaging, first check whether the channel exposes the verified-account desktop Studio custom-thumbnail control. If available, prepare a dedicated 9:16 thumbnail asset and treat it as a packaging variable. If unavailable, fall back to an intentional in-video frame. Do not claim the custom thumbnail was applied until Studio/remote state is read back.
- test_next_measurement: On the next eligible Short, inspect the channel's desktop Studio control. If present, upload a dedicated 9:16 thumbnail, save, then read back/visually verify the remote thumbnail. Compare subsequent packaging performance using appropriate Shorts metrics; do not call this a native A/B test because Shorts native A/B testing remains separately constrained.
- discovered_at: 2026-10-02
- last_verified: 2026-10-02
- access_status: `web_only`
- failure_history: none for source retrieval; channel-level feature availability not yet tested
- fallback: intentional frame selection from the Short when custom upload is unavailable
- provenance: official YouTube Help, primary source
- first_added_cycle: 2026-10-02-cycle-09
- last_used_cycle: 2026-10-02-cycle-09
- use_count: 1
- status: active
- persistence_status: pending read-back at write time
- bridge_status: pending real Video/Shopify consumption

## Decision value

This changes production planning: Shorts can now have a purpose-built vertical packaging asset when the verified desktop Studio feature is actually available. It should be planned during storyboard/packaging rather than assuming the selected video frame is the only thumbnail option.
