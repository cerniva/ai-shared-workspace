import json, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from policy import PolicyViolation, enforce_action, normalize_allow_hosts, safe_url

ART = Path(os.getenv("BROWSER_ARTIFACTS", "browser-artifacts"))
ART.mkdir(parents=True, exist_ok=True)
SENSITIVE_HINTS = ("password", "passwd", "secret", "token", "api_key", "credit card", "card number", "cvv", "cvc", "otp", "2fa")


def target(page, step):
    if step.get("role"):
        loc = page.get_by_role(step["role"], name=step.get("name"), exact=step.get("exact", False))
    elif step.get("label"):
        loc = page.get_by_label(step["label"], exact=step.get("exact", False))
    elif step.get("text"):
        loc = page.get_by_text(step["text"], exact=step.get("exact", False))
    elif step.get("selector"):
        loc = page.locator(step["selector"])
    else:
        raise ValueError("step needs role/name, label, text or selector")
    return loc.first


def step_label(step):
    return " ".join(str(step.get(k, "")) for k in ("role", "name", "label", "text", "selector")).strip()


def main(task_path):
    task = json.loads(Path(task_path).read_text(encoding="utf-8"))
    steps = task.get("steps", [])
    if not isinstance(steps, list) or len(steps) > 20:
        raise ValueError("task must contain at most 20 steps")
    allowed_hosts = normalize_allow_hosts(os.getenv("BROWSER_ALLOWED_HOSTS", ""))
    mode = os.getenv("BROWSER_EXECUTION_MODE", "read_only").lower()
    if mode not in {"read_only", "interactive"}:
        raise ValueError("BROWSER_EXECUTION_MODE must be read_only or interactive")
    result = {"id": task.get("id"), "status": "running", "events": [], "mode": mode, "allowed_hosts": sorted(allowed_hosts)}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.getenv("HEADLESS", "1") != "0")
        context = browser.new_context()

        def guard_request(route):
            try:
                safe_url(route.request.url, allowed_hosts)
                route.continue_()
            except PolicyViolation:
                route.abort("blockedbyclient")

        context.route("**/*", guard_request)
        page = context.new_page()
        for i, step in enumerate(steps):
            action = str(step.get("action", "")).lower()
            try:
                label = step_label(step)
                field_attrs = {}
                if action in {"fill", "type"}:
                    hint = label.lower()
                    if any(term in hint for term in SENSITIVE_HINTS):
                        raise PolicyViolation("approval_required: sensitive fields are never filled by this worker")
                    loc = target(page, step)
                    field_attrs = {
                        name: loc.get_attribute(name)
                        for name in ("type", "name", "id", "placeholder", "autocomplete", "aria-label")
                    }
                enforce_action(action, mode, label, field_attrs, key=str(step.get("key", "")))

                if action == "goto":
                    page.goto(safe_url(step["url"], allowed_hosts), wait_until="domcontentloaded", timeout=30000)
                    safe_url(page.url, allowed_hosts)
                elif action == "click":
                    target(page, step).click(timeout=15000)
                    safe_url(page.url, allowed_hosts)
                elif action in ("fill", "type"):
                    target(page, step).fill(str(step.get("value", "")), timeout=15000)
                elif action == "press":
                    target(page, step).press(step["key"], timeout=15000)
                elif action == "wait":
                    page.wait_for_timeout(min(max(int(step.get("ms", 1000)), 0), 10000))
                elif action == "wait_for":
                    target(page, step).wait_for(state=step.get("state", "visible"), timeout=min(max(int(step.get("timeout", 15000)), 1), 30000))
                elif action == "screenshot":
                    page.screenshot(path=str(ART / f'{task.get("id", "task")}-{i}.png'), full_page=True)
                elif action == "extract":
                    text = target(page, step).inner_text()[:10000]
                    result["events"].append({"step": i, "action": "extract", "text": text})
                else:
                    raise PolicyViolation(f"unsupported browser action: {action}")

                result["events"].append({"step": i, "action": action, "url": page.url, "title": page.title()[:200], "ok": True})
            except Exception as exc:
                try:
                    page.screenshot(path=str(ART / f'{task.get("id", "task")}-error-{i}.png'), full_page=True)
                except Exception:
                    pass
                message = str(exc)
                if isinstance(exc, PolicyViolation) and "approval_required:" in message:
                    status = "needs_human"
                elif isinstance(exc, PolicyViolation):
                    status = "blocked"
                elif any(term in message.lower() for term in ("captcha", "2fa", "verification")):
                    status = "needs_human"
                else:
                    status = "failed"
                result.update(status=status, error=message, failed_step=i)
                break
        else:
            result["status"] = "done"

        Path(ART / f'{task.get("id", "task")}-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "done" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
