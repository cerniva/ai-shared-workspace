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

def _sanitize_provider_error(text):
    text=(text or "").strip()
    for name in ("OPENAI_API_KEY","XAI_API_KEY","GEMINI_API_KEY","ANTHROPIC_API_KEY","ANTHROPIC_AUTH_TOKEN","ANTHROPIC_IDENTITY_TOKEN"):
        secret=os.getenv(name,"").strip()
        if secret: text=text.replace(secret,"***")
    return text[:2000]

def _post(url, headers, payload, timeout=90):
    req=Request(url,data=json.dumps(payload).encode("utf-8"),headers={"Content-Type":"application/json",**headers},method="POST")
    try:
        with urlopen(req,timeout=timeout) as r: return json.load(r)
    except HTTPError as exc:
        try: body=exc.read().decode("utf-8","replace")
        except Exception: body=""
        body=_sanitize_provider_error(body)
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}"+((": "+body) if body else "")) from exc

def _openai(objective):
    key=os.getenv("OPENAI_API_KEY","").strip()
    if not key: raise RuntimeError("OPENAI_API_KEY missing")
    model=os.getenv("OPENAI_MODEL","gpt-5.6-sol")
    data=_post("https://api.openai.com/v1/responses",{"Authorization":"Bearer "+key},{"model":model,"input":SYSTEM+"\nOBJECTIVE:\n"+objective,"reasoning":{"effort":"medium"},"store":False})
    return _clean("".join(p.get("text","") for o in data.get("output",[]) if o.get("type")=="message" for p in o.get("content",[]) if p.get("type")=="output_text"))

def _grok(objective):
    key=os.getenv("XAI_API_KEY","").strip()
    if not key: raise RuntimeError("XAI_API_KEY missing")
    model=os.getenv("XAI_MODEL","grok-4.7")
    data=_post("https://api.x.ai/v1/responses",{"Authorization":"Bearer "+key},{"model":model,"input":SYSTEM+"\nOBJECTIVE:\n"+objective,"store":False})
    return _clean("".join(p.get("text","") for o in data.get("output",[]) if o.get("type")=="message" for p in o.get("content",[]) if p.get("type")=="output_text"))

def _gemini(objective):
    key=os.getenv("GEMINI_API_KEY","").strip()
    if not key: raise RuntimeError("GEMINI_API_KEY missing")
    model=os.getenv("GEMINI_MODEL","gemini-3.8-flash")
    data=_post("https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent",{"x-goog-api-key":key},{"contents":[{"parts":[{"text":SYSTEM+"\nOBJECTIVE:\n"+objective}]}]})
    candidates=data.get("candidates") or []
    text="" if not candidates else "".join(str(p.get("text","")) for p in (candidates[0].get("content") or {}).get("parts",[]) if "text" in p)
    return _clean(text)

def _anthropic_auth_headers():
    key=os.getenv("ANTHROPIC_API_KEY","").strip(); workspace_id=os.getenv("ANTHROPIC_WORKSPACE_ID","").strip()
    if key:
        headers={"x-api-key":key,"anthropic-version":"2023-06-01"}
        if workspace_id: headers["anthropic-workspace-id"]=workspace_id
        return headers
    auth_token=os.getenv("ANTHROPIC_AUTH_TOKEN","").strip()
    if auth_token: return {"Authorization":"Bearer "+auth_token,"anthropic-version":"2023-06-01"}
    raise RuntimeError("Anthropic auth missing")

def _anthropic(objective):
    model=os.getenv("ANTHROPIC_MODEL","claude-opus-5-5")
    data=_post("https://api.anthropic.com/v1/messages",_anthropic_auth_headers(),{"model":model,"max_tokens":4096,"system":SYSTEM,"messages":[{"role":"user","content":"OBJECTIVE:\n"+objective}]})
    return _clean("".join(str(block.get("text","")) for block in data.get("content",[]) if block.get("type")=="text"))

def _providers():
    return (("openai",_openai),("grok",_grok),("gemini",_gemini),("anthropic",_anthropic))

def plan(objective, provider=None):
    provider=(provider or os.getenv("BROWSER_PLANNER_PROVIDER","auto")).strip().lower()
    if provider=="claude": provider="anthropic"
    providers=_providers(); provider_map=dict(providers)
    if provider=="auto": selected=providers
    elif provider in provider_map:
        # A preferred provider is tried first, but no longer becomes a single point of failure.
        selected=((provider,provider_map[provider]),)+tuple(item for item in providers if item[0]!=provider)
    else: raise ValueError("unsupported planner provider: "+provider)
    errors=[]
    for name,fn in selected:
        try:
            task=fn(objective); task["planner_provider"]=name; return task
        except (HTTPError,URLError,TimeoutError,RuntimeError,ValueError,json.JSONDecodeError) as exc:
            status=getattr(exc,"code",None); errors.append(name+":"+((str(status)+" ") if status else "")+str(exc)); print("planner fallback: "+errors[-1],file=sys.stderr)
    raise SystemExit("all planner providers failed: "+" | ".join(errors))

if __name__=="__main__":
    objective=os.getenv("BROWSER_OBJECTIVE") or " ".join(sys.argv[1:])
    if not objective: raise SystemExit("objective is required")
    print(json.dumps(plan(objective),ensure_ascii=False))
