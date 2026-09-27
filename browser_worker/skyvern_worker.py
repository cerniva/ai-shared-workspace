import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    from .policy import PolicyViolation, normalize_allow_hosts, safe_url
except ImportError:
    from policy import PolicyViolation, normalize_allow_hosts, safe_url

ART = Path(os.getenv("BROWSER_ARTIFACTS", "browser-artifacts"))
ART.mkdir(parents=True, exist_ok=True)
SKYVERN_READ_ONLY_ACTIONS = {"goto", "extract", "screenshot", "wait", "wait_for"}


def adapt_task(task):
    """Convert explicit Skyvern or deterministic planner tasks to one safe read-only run."""
    if not isinstance(task, dict):
        raise ValueError("skyvern task must be a JSON object")

    url = str(task.get("url") or "").strip()
    prompt = str(task.get("goal") or task.get("prompt") or "").strip()
    steps = task.get("steps")

    if steps is not None:
        if not isinstance(steps, list) or not steps:
            raise ValueError("skyvern task steps must be a non-empty list")
        actions = [str(step.get("action") or "").lower() for step in steps if isinstance(step, dict)]
        if len(actions) != len(steps):
            raise ValueError("every skyvern step must be an object")
        unsupported = sorted(set(actions) - SKYVERN_READ_ONLY_ACTIONS)
        if unsupported:
            raise PolicyViolation(
                "approval_required: Skyvern only accepts read-only planner steps; "
                f"blocked actions: {', '.join(unsupported)}"
            )

        goto_urls = [
            str(step.get("url") or "").strip()
            for step in steps
            if str(step.get("action") or "").lower() == "goto"
        ]
        if not url:
            unique_urls = list(dict.fromkeys(value for value in goto_urls if value))
            if len(unique_urls) != 1:
                raise ValueError("skyvern planner task needs exactly one goto URL")
            url = unique_urls[0]

        if not prompt:
            requests = []
            for step in steps:
                action = str(step.get("action") or "").lower()
                if action == "extract":
                    target = (
                        step.get("selector")
                        or step.get("text")
                        or step.get("label")
                        or step.get("name")
                        or "the requested page content"
                    )
                    requests.append(f"extract {target!r}")
                elif action == "screenshot":
                    requests.append("capture a screenshot")
                elif action == "wait_for":
                    target = step.get("selector") or step.get("text") or step.get("label") or "the requested element"
                    requests.append(f"wait for {target!r}")
            if not requests:
                requests.append("read the page")
            prompt = "Read-only task: " + "; ".join(requests) + ". Do not click, type, submit, publish, purchase, or change data."

    if not url:
        raise ValueError("skyvern task needs url or one goto step")
    if not prompt:
        raise ValueError("skyvern task needs goal, prompt, or readable planner steps")
    return url, prompt


async def run(task_path):
    from skyvern import Skyvern

    task = json.loads(Path(task_path).read_text(encoding="utf-8"))
    allowed_hosts = normalize_allow_hosts(os.getenv("BROWSER_ALLOWED_HOSTS", ""))
    raw_url, prompt = adapt_task(task)
    url = safe_url(raw_url, allowed_hosts)
    max_steps = min(max(int(task.get("max_steps", 10)), 1), 20)

    client = Skyvern(api_key=os.environ["SKYVERN_API_KEY"])
    result = await client.run_task(
        prompt=prompt,
        url=url,
        wait_for_completion=True,
        max_steps=max_steps,
    )
    status = str(getattr(result, "status", "unknown"))
    output = getattr(result, "output", None)
    payload = {
        "id": task.get("id"),
        "engine": "skyvern",
        "status": "done" if "completed" in status.lower() else "failed",
        "provider_status": status,
        "output": output,
        "host": urlparse(url).hostname,
    }
    Path(ART / f'{task.get("id", "task")}-skyvern-result.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, default=str))
    return 0 if payload["status"] == "done" else 2


def main(task_path):
    try:
        return asyncio.run(run(task_path))
    except (PolicyViolation, ValueError, KeyError) as exc:
        print(json.dumps({"status": "blocked", "engine": "skyvern", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
