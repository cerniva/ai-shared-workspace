import json, os, sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SYSTEM = """Convert the user's authorized browser objective into deterministic Playwright worker steps.
Return ONLY JSON: {"id":"ai-browser","steps":[...]}.
Allowed actions: goto, click, fill, type, press, wait, wait_for, extract, screenshot.
Prefer role/name or label locators; selector only when necessary.
Never invent credentials. Never put passwords, API keys, tokens, card data, CAPTCHA answers, or 2FA codes in steps.
Do not create payment, financial transaction, account-security, permission-change, destructive delete, checkout/refund, price-write, or publish steps.
For login/authentication boundaries, navigate to the page if useful but stop before entering secrets and end with a screenshot.
Use only http/https URLs explicitly present in the objective or clearly required by the named public site.
"""

def _clean(text):
    text=text.strip()
    if text.startswith("```"):
        lines=text.splitlines()
        text="\n".join(lines[1:-1]).strip()
    task=json.loads(text)
    if not isinstance(task,dict) or not isinstance(task.get("steps"),list):
        raise ValueError("planner returned invalid task")
    return task

def _post(url, headers, payload, timeout=90):
    req=Request(url,data=json.dumps(payload).encode("utf-8"),headers={"Content-Type":"application/json",**headers},method="POST")
    with urlopen(req,timeout=timeout) as r:
        return json.load(r)

def _openai(objective):
    key=os.getenv("OPENAI_API_KEY","").strip()
    if not key: raise RuntimeError("OPENAI_API_KEY missing")
    model=os.getenv("OPENAI_MODEL","gpt-5.6-sol")
    data=_post("https://api.openai.com/v1/responses",{"Authorization":"Bearer "+key},{"model":model,"input":SYSTEM+"\nOBJECTIVE:\n"+objective,"reasoning":{"effort":"medium"},"store":False})
    text="".join(p.get("text","") for o in data.get("output",[]) if o.get("type")=="message" for p in o.get("content",[]) if p.get("type")=="output_text")
    return _clean(text)

def _grok(objective):
    key=os.getenv("XAI_API_KEY","").strip()
    if not key: raise RuntimeError("XAI_API_KEY missing")
    model=os.getenv("XAI_MODEL","grok-4.7")
    data=_post("https://api.x.ai/v1/responses",{"Authorization":"Bearer "+key},{"model":model,"input":SYSTEM+"\nOBJECTIVE:\n"+objective,"store":False})
    text="".join(p.get("text","") for o in data.get("output",[]) if o.get("type")=="message" for p in o.get("content",[]) if p.get("type")=="output_text")
    return _clean(text)

def _gemini(objective):
    key=os.getenv("GEMINI_API_KEY","").strip()
    if not key: raise RuntimeError("GEMINI_API_KEY missing")
    model=os.getenv("GEMINI_MODEL","gemini-3.8-flash")
    data=_post("https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent",{"x-goog-api-key":key},{"contents":[{"parts":[{"text":SYSTEM+"\nOBJECTIVE:\n"+objective}]}]})
    candidates=data.get("candidates") or []
    text=""
    if candidates:
        text="".join(str(p.get("text","")) for p in (candidates[0].get("content") or {}).get("parts",[]) if "text" in p)
    return _clean(text)

def plan(objective):
    errors=[]
    for name,fn in (("openai",_openai),("grok",_grok),("gemini",_gemini)):
        try:
            task=fn(objective)
            task["planner_provider"]=name
            return task
        except (HTTPError,URLError,TimeoutError,RuntimeError,ValueError,json.JSONDecodeError) as exc:
            status=getattr(exc,"code",None)
            errors.append(name+":"+((str(status)+" ") if status else "")+str(exc))
            print("planner fallback: "+errors[-1],file=sys.stderr)
    raise SystemExit("all planner providers failed: "+" | ".join(errors))

if __name__=="__main__":
    objective=os.getenv("BROWSER_OBJECTIVE") or " ".join(sys.argv[1:])
    if not objective: raise SystemExit("objective is required")
    print(json.dumps(plan(objective),ensure_ascii=False))
