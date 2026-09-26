import json, os, sys, time
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ART=Path(os.getenv("BROWSER_ARTIFACTS","browser-artifacts")); ART.mkdir(parents=True,exist_ok=True)
BLOCKED={"file","javascript","data"}
SENSITIVE=("password","passwd","secret","token","api_key","credit card","card number","cvv")

def safe_url(url):
    p=urlparse(url)
    if p.scheme not in ("http","https"): raise ValueError("Only http/https URLs are allowed")
    return url

def target(page, step):
    if step.get("role"):
        loc=page.get_by_role(step["role"], name=step.get("name"), exact=step.get("exact",False))
    elif step.get("label"):
        loc=page.get_by_label(step["label"], exact=step.get("exact",False))
    elif step.get("text"):
        loc=page.get_by_text(step["text"], exact=step.get("exact",False))
    elif step.get("selector"):
        loc=page.locator(step["selector"])
    else: raise ValueError("step needs role/name, label, text or selector")
    return loc.first

def main(task_path):
    task=json.loads(Path(task_path).read_text())
    steps=task.get("steps",[])
    result={"id":task.get("id"),"status":"running","events":[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=os.getenv("HEADLESS","1")!="0")
        context=browser.new_context(storage_state=os.getenv("STORAGE_STATE") if os.getenv("STORAGE_STATE") and Path(os.getenv("STORAGE_STATE")).exists() else None)
        page=context.new_page()
        for i,s in enumerate(steps):
            action=s.get("action","").lower()
            try:
                if action=="goto": page.goto(safe_url(s["url"]),wait_until="domcontentloaded",timeout=30000)
                elif action=="click": target(page,s).click(timeout=15000)
                elif action in ("fill","type"):
                    val=str(s.get("value",""))
                    hint=" ".join(str(s.get(k,"")) for k in ("label","name","selector")).lower()
                    if any(x in hint for x in SENSITIVE) and not s.get("allow_sensitive",False):
                        raise RuntimeError("sensitive field requires explicit allow_sensitive and secret injection")
                    target(page,s).fill(val,timeout=15000)
                elif action=="press": target(page,s).press(s["key"])
                elif action=="wait": page.wait_for_timeout(int(s.get("ms",1000)))
                elif action=="wait_for": target(page,s).wait_for(state=s.get("state","visible"),timeout=int(s.get("timeout",15000)))
                elif action=="screenshot": page.screenshot(path=str(ART/f'{task.get("id","task")}-{i}.png'),full_page=True)
                elif action=="extract":
                    result["events"].append({"step":i,"action":"extract","text":target(page,s).inner_text()[:10000]})
                else: raise ValueError(f"unsupported action: {action}")
                result["events"].append({"step":i,"action":action,"url":page.url,"title":page.title()[:200],"ok":True})
            except Exception as e:
                page.screenshot(path=str(ART/f'{task.get("id","task")}-error-{i}.png'),full_page=True)
                result.update(status="needs_human" if any(x in str(e).lower() for x in ("captcha","2fa","verification","sensitive")) else "failed",error=str(e),failed_step=i)
                break
        else: result["status"]="done"
        Path(ART/f'{task.get("id","task")}-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        browser.close()
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result["status"]=="done" else 2
if __name__=="__main__": sys.exit(main(sys.argv[1]))
