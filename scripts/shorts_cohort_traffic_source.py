"""Shorts cohort traffic-source gates.

Official dimensions checked 2026-10-04:
https://developers.google.com/youtube/analytics/dimensions

Does not query a channel, invent metrics, or touch PayoutLens.
Existing story_phase / retention / A/V / Shopify gates are not modified.
"""

from __future__ import annotations

DETAIL_MEANING = {
    "ADVERTISING": "ad_type",
    "EXT_URL": "web_page_includes_google_search_referrals",
    "RELATED_VIDEO": "referring_video_id",
    "SUBSCRIBER": "homepage_or_subscription_page",
    "YT_CHANNEL": "channel_id",
    "YT_OTHER_PAGE": "youtube_page",
    "YT_SEARCH": "search_term",
    "VIDEO_REMIXES": "referring_remixed_video_id",
    "WATCH_WITH": "referring_video_id",
}

# Distinct from insightTrafficSourceType=SHORTS (vertical swipe).
SHORTS_ADJACENT = {"HASHTAGS", "SOUND_PAGE", "VIDEO_REMIXES"}


def _blank(value) -> bool:
    return value is None or value == "" or value == "unknown"


def classify_cohort_traffic(row: dict) -> dict:
    """Classify one cohort row. Missing source stays unknown."""
    source = row.get("insightTrafficSourceType")
    detail = row.get("insightTrafficSourceDetail")
    content_type = row.get("creatorContentType")
    if _blank(source):
        return {
            "gate": "SHORTS_COHORT_TRAFFIC_SOURCE_GATE",
            "status": "unknown",
            "source_type": None,
            "detail": None,
            "detail_applicable": False,
            "reason": "authorized traffic source missing; raw views are not a source mix",
            "content_type_is_source": False,
        }
    if content_type == "SHORTS" and source != "SHORTS":
        content_note = "creatorContentType SHORTS is not the traffic source"
    else:
        content_note = None
    if source == "SHORTS":
        if not _blank(detail):
            return {
                "gate": "SHORTS_COHORT_TRAFFIC_SOURCE_GATE",
                "status": "reject",
                "source_type": "SHORTS",
                "detail": None,
                "detail_applicable": False,
                "reason": "SHORTS detail is not defined; do not infer a swipe referrer",
                "content_type_is_source": False,
            }
        return {
            "gate": "SHORTS_COHORT_TRAFFIC_SOURCE_GATE",
            "status": "accept",
            "source_type": "SHORTS",
            "detail": None,
            "detail_applicable": False,
            "reason": "vertical swipe in the Shorts viewing experience; detail not applicable",
            "content_type_is_source": False,
        }
    if source in DETAIL_MEANING:
        if _blank(detail):
            return {
                "gate": "SHORTS_COHORT_TRAFFIC_SOURCE_GATE",
                "status": "accept",
                "source_type": source,
                "detail": None,
                "detail_meaning": DETAIL_MEANING[source],
                "detail_applicable": True,
                "reason": "source type accepted; detail unknown until an authorized value exists",
                "content_type_is_source": False,
                "note": content_note,
            }
        return {
            "gate": "SHORTS_COHORT_TRAFFIC_SOURCE_GATE",
            "status": "accept",
            "source_type": source,
            "detail": detail,
            "detail_meaning": DETAIL_MEANING[source],
            "detail_applicable": True,
            "reason": "detail kept with documented source-specific meaning only",
            "content_type_is_source": False,
            "causal": False,
            "note": content_note,
        }
    if not _blank(detail):
        return {
            "gate": "SHORTS_COHORT_TRAFFIC_SOURCE_GATE",
            "status": "reject",
            "source_type": source,
            "detail": None,
            "detail_applicable": False,
            "reason": "detail is not documented for this source type",
            "content_type_is_source": False,
        }
    reason = "source type only; detail not documented"
    if source in SHORTS_ADJACENT:
        reason = "Shorts-adjacent source is not the vertical-swipe SHORTS source"
    return {
        "gate": "SHORTS_COHORT_TRAFFIC_SOURCE_GATE",
        "status": "accept",
        "source_type": source,
        "detail": None,
        "detail_applicable": False,
        "reason": reason,
        "content_type_is_source": False,
        "note": content_note,
    }
