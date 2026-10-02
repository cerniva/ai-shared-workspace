"""Watch-page subscriber conversion math. No network and no secrets."""

from __future__ import annotations


def watch_page_net_subscribers(subscribers_gained: int, subscribers_lost: int) -> int:
    return int(subscribers_gained) - int(subscribers_lost)


def net_subscribers_per_1000_engaged_views(
    subscribers_gained: int,
    subscribers_lost: int,
    engaged_views: int,
) -> float | None:
    views = int(engaged_views)
    if views <= 0:
        return None
    net = watch_page_net_subscribers(subscribers_gained, subscribers_lost)
    return round(net * 1000 / views, 4)


def video_subscriber_report_params(video_id: str) -> dict[str, str]:
    video_id = video_id.strip()
    if not video_id or any(ch in video_id for ch in " ,;&="):
        raise ValueError("video_id must be a single id")
    return {
        "filters": f"video=={video_id}",
        "metrics": "subscribersGained,subscribersLost,engagedViews",
        "label": "watch-page-attributed",
    }
