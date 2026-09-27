import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from policy import PolicyViolation, normalize_allow_hosts, safe_url

ART = Path(os.getenv("BROWSER_ARTIFACTS", "browser-artifacts"))
ART.mkdir(parents=True, exist_ok=True)


def _goto_url(task):
    direct = str(task.get("url") or "").strip()
    if direct:
        return direct
    for step in task.get("steps") or []:
        if str(step.get("action", "")).lower() == "goto" and step.get("url"):
            return str(step["url"]).strip()
    raise ValueError("skyvern task needs a top-level url or a goto step")


def build_prompt(task):
    goal = str(task.get("goal") or task.get("prompt") or "").strip()
    if goal:
        return goal
    objective = str(os.getenv("BROWSER_OBJECTIVE", "")).strip()
    if objective:
        return objective
    steps = task.get("steps") or []
    if steps:
        return "Execute this browser plan: " + json.dumps(steps, ensure_ascii=False)
    raise ValueError("skyvern task needs goal, prompt, objective, or steps")


async def run(task_path):
    from skyvern import Skyvern

    task = json.loads(Path(task_path).read_text(encoding="utf-8"))
    allowed_hosts = normalize_allow_hosts(os.getenv("BROWSER_ALLOWED_HOSTS", ""))
    url = safe_url(_goto_url(task), allowed_hosts)
    prompt = build_prompt(task)
    max_steps = min(max(int(task.get("max_steps", 10)), 1), 20)

    api_key = os.getenv("SKYVERN_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("SKYVERN_API_KEY is not configured")

    client = Skyvern(api_key=api_key)
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
    except PolicyViolation as exc:
        print(json.dumps({"status": "blocked", "engine": "skyvern", "error": str(exc)}, ensure_ascii=False))
        return 2
    except (KeyError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "failed", "engine": "skyvern", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
