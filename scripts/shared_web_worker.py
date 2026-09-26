#!/usr/bin/env python3
"""Firecrawl keyless fallback for the shared TinyFish web worker."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from scripts import tinyfish_senses as tiny

FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"
FALLBACK_REASON_CODES = {"transient", "credits-plan"}
_original_execute_task = tiny.execute_task

browser_block_reason = tiny.browser_block_reason
classify_http_status = tiny.classify_http_status


def _post_json(url: str, payload: dict[str, Any], timeout: int = 90) -> dict[str, Any]:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST", headers={"Content-Type": "application/json", "User-Agent": "cerniva-desk-web-worker/1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def firecrawl_fetch(urls: list[str]) -> dict[str, Any]:
    pages = []
    for url in urls:
        response = _post_json(FIRECRAWL_SCRAPE_URL, {"url": url, "formats": ["markdown"], "maxAge": 0})
        data = response.get("data", response) if isinstance(response, dict) else response
        pages.append({"url": url, "data": data})
    return {"pages": pages}


def build_firecrawl_browser_request(task: dict[str, object]) -> tuple[str, dict[str, Any]]:
    if task.get("mode") != "browser":
        raise ValueError("Firecrawl browser fallback requires mode: browser")
    reason = tiny.browser_block_reason(task)
    if reason:
        raise ValueError(reason)
    url = str(task.get("url", "")); goal = str(task.get("goal", ""))
    if not url or not goal:
        raise ValueError("Firecrawl browser fallback requires url and goal")
    return url, {"prompt": goal}


def firecrawl_browser(url: str, goal: str) -> dict[str, Any]:
    opened = _post_json(FIRECRAWL_SCRAPE_URL, {"url": url, "formats": ["markdown"], "maxAge": 0})
    data = opened.get("data", {}) if isinstance(opened, dict) else {}
    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
    scrape_id = metadata.get("scrapeId") or metadata.get("scrape_id")
    if not scrape_id:
        raise RuntimeError("Firecrawl scrape response missing scrapeId")
    return _post_json(f"{FIRECRAWL_SCRAPE_URL}/{scrape_id}/interact", {"prompt": goal}, timeout=120)


def _fallback(task: dict[str, object], ledger: dict | None) -> tuple[str, object, str]:
    try:
        if task.get("mode") == "fetch":
            result = firecrawl_fetch(list(task.get("urls", [])))
        else:
            url, payload = build_firecrawl_browser_request(task)
            result = firecrawl_browser(url, str(payload["prompt"]))
        if ledger is not None:
            record = tiny.record_terminal(ledger, str(task.get("id", "")), "done", ""); record["provider"] = "firecrawl"
        return "done", {"provider": "firecrawl", "result": result}, ""
    except urllib.error.HTTPError as exc:
        reason = f"Firecrawl HTTP {exc.code}"; retryable = exc.code == 429 or exc.code >= 500
        if ledger is not None:
            record = tiny.record_terminal(ledger, str(task.get("id", "")), "retryable" if retryable else "blocked", reason); record["provider"] = "firecrawl"
        return ("retryable" if retryable else "blocked"), {"provider": "firecrawl", "http_status": exc.code, "reason_code": "fallback-http-error"}, reason
    except Exception as exc:
        reason = str(exc)[:200]
        if ledger is not None:
            record = tiny.record_terminal(ledger, str(task.get("id", "")), "blocked", reason); record["provider"] = "firecrawl"
        return "blocked", {"provider": "firecrawl", "reason_code": "fallback-runtime-error"}, reason


def execute_task(task: dict[str, object], key: str, ledger: dict | None = None) -> tuple[str, object, str]:
    status, data, reason = _original_execute_task(task, key, ledger=ledger)
    reason_code = data.get("reason_code", "") if isinstance(data, dict) else ""
    if reason_code not in FALLBACK_REASON_CODES:
        return status, data, reason
    return _fallback(task, ledger)


def fallback_needed(record: dict | None) -> bool:
    if not record:
        return False
    if record.get("status") == "retryable":
        return True
    return record.get("status") == "blocked" and "credits/plan required" in str(record.get("last_error", "")).lower()


def fallback_main() -> int:
    block = tiny.latest_task(tiny.INBOX.read_text(encoding="utf-8") if tiny.INBOX.exists() else "")
    task = tiny.parse_task(block); task_id = str(task.get("id", ""))
    ledger = tiny.load_ledger(); record = tiny.task_record(ledger, task_id)
    if not fallback_needed(record):
        return 0
    valid, reason = tiny.validate_task(task)
    if not valid or (task.get("mode") == "browser" and tiny.browser_block_reason(task)):
        return 0
    status, data, reason = _fallback(task, ledger)
    tiny.save_ledger(ledger); tiny.append_result(task, status, data)
    if status == "done":
        tiny.mark_inbox("done", "firecrawl fallback ok")
    elif status == "retryable":
        tiny.mark_inbox("retryable", reason or "Firecrawl transient error")
    else:
        tiny.mark_inbox("blocked", reason or "Firecrawl fallback failed")
    return 0


def main() -> int:
    return fallback_main()


if __name__ == "__main__":
    raise SystemExit(main())
