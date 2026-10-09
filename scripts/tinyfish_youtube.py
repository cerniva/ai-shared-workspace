#!/usr/bin/env python3
"""YouTube via TinyFish's saved logged-in browser (Browser Context Profile).

TinyFish here is a hosted web agent (agent.tinyfish.ai, secret TINYFISH_API_KEY).
"Connected" YouTube/Google means a Browser Context Profile signed into those
sites; a run passes ``use_profile: true`` (optionally ``profile_id``) to start
already logged in. Docs: https://docs.tinyfish.ai/agent-api/reference

What this adapter does:
- ``analytics``: read-only YouTube Studio analytics run with structured output.
  Dry-run (prints the request) unless ``--execute``; never sends without a key.
- ``upload-route``: decides the Shorts upload path. The YouTube Data API
  (YOUTUBE_* OAuth secrets) is the only upload route. A hosted TinyFish browser
  cannot receive the MP4 rendered on the GitHub runner (no file transfer in the
  Agent API) and PROTOCOL blocks public publishing through browser agents, so
  without OAuth secrets the route is BLOCKED, never a fake success.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import Any, Mapping

RUN_URL = "https://agent.tinyfish.ai/v1/automation/run"
STUDIO_URL = "https://studio.youtube.com/"
YOUTUBE_OAUTH_ENV = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
PROFILE_ENV = "TINYFISH_YOUTUBE_PROFILE_ID"
ALLOWED_PRIVACY = {"private", "unlisted"}

ANALYTICS_SCHEMA = {
    "type": "object",
    "properties": {
        "channel_name": {"type": "string"},
        "period": {"type": "string"},
        "views": {"type": "number"},
        "watch_time_hours": {"type": "number"},
        "subscribers_change": {"type": "number"},
        "top_videos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"title": {"type": "string"}, "views": {"type": "number"}},
            },
        },
    },
    "required": ["channel_name", "period", "views"],
}


def analytics_payload(period: str = "Last 28 days", env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = os.environ if env is None else env
    payload: dict[str, Any] = {
        "url": STUDIO_URL,
        "goal": (
            f"READ ONLY. Open YouTube Studio Analytics for the signed-in channel, select '{period}', "
            "and extract channel name, period, views, watch time (hours), subscriber change and the top "
            "5 videos with views. Do not upload, edit, publish, delete, comment or change any setting. "
            "If not signed in or a login/2FA/CAPTCHA appears, stop and report NOT_SIGNED_IN."
        ),
        "output_schema": ANALYTICS_SCHEMA,
        "browser_profile": "stealth",
        "use_profile": True,
    }
    profile_id = str(env.get(PROFILE_ENV, "")).strip()
    if profile_id:
        payload["profile_id"] = profile_id
    return payload


def upload_route(env: Mapping[str, str] | None = None, privacy: str = "private") -> dict[str, Any]:
    env = os.environ if env is None else env
    if privacy not in ALLOWED_PRIVACY:
        return {"route": "blocked", "reason": "privacy must be private or unlisted", "privacy": privacy}
    missing = [name for name in YOUTUBE_OAUTH_ENV if not str(env.get(name, "")).strip()]
    if not missing:
        return {"route": "youtube_api", "privacy": privacy, "missing": []}
    return {
        "route": "blocked",
        "privacy": privacy,
        "missing": missing,
        "reason": (
            "YouTube OAuth secrets missing. TinyFish browser profile cannot upload: the Agent API has no "
            "file transfer from the runner and browser publishing is blocked by PROTOCOL."
        ),
    }


def run(payload: dict[str, Any], key: str, opener=urllib.request.urlopen) -> dict[str, Any]:
    req = urllib.request.Request(
        RUN_URL, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": key, "User-Agent": "cerniva-desk-tinyfish-youtube/1"},
    )
    with opener(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main(argv: list[str] | None = None, env: Mapping[str, str] | None = None, opener=urllib.request.urlopen) -> int:
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analytics")
    a.add_argument("--period", default="Last 28 days")
    a.add_argument("--execute", action="store_true", help="actually call TinyFish (default: dry-run)")
    u = sub.add_parser("upload-route")
    u.add_argument("--privacy", default="private")
    args = parser.parse_args(argv)
    if args.cmd == "upload-route":
        decision = upload_route(env, args.privacy)
        print(json.dumps(decision))
        return 0 if decision["route"] == "youtube_api" else 3
    payload = analytics_payload(args.period, env)
    if not args.execute:
        print(json.dumps({"dry_run": True, "endpoint": RUN_URL, "payload": payload}, ensure_ascii=False))
        return 0
    key = str(env.get("TINYFISH_API_KEY", "")).strip()
    if not key:
        print(json.dumps({"status": "blocked", "reason_code": "missing-secret", "secret": "TINYFISH_API_KEY"}))
        return 2
    result = run(payload, key, opener)
    print(json.dumps({"status": result.get("status"), "run_id": result.get("run_id"),
                      "result": result.get("result"), "error": result.get("error")}, ensure_ascii=False))
    return 0 if result.get("status") == "COMPLETED" else 1


if __name__ == "__main__":
    sys.exit(main())
