import json, os, re

objective = os.getenv("BROWSER_OBJECTIVE", "").strip()
urls = re.findall(r"https?://[^\s]+", objective)
if not urls:
    raise SystemExit("local fallback requires an explicit http/https URL")

url = urls[0].rstrip(".,);]}>\"")
lower = objective.lower()
steps = [{"action": "goto", "url": url}]

if "başlık" in lower or "title" in lower:
    steps.append({"action": "extract", "selector": "title"})

if "ekran görüntüsü" in lower or "screenshot" in lower or "görüntü al" in lower:
    steps.append({"action": "screenshot"})

if len(steps) == 1:
    steps.append({"action": "screenshot"})

print(json.dumps({"id": "ai-browser-local", "planner_provider": "local-basic", "steps": steps}, ensure_ascii=False))
