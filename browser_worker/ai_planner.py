import json, os, sys
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

def plan(objective):
    key=os.getenv("OPENAI_API_KEY","").strip()
    if not key: raise SystemExit("OPENAI_API_KEY is missing")
    model=os.getenv("OPENAI_MODEL","gpt-5.6-sol")
    payload={"model":model,"input":SYSTEM+"\nOBJECTIVE:\n"+objective,"reasoning":{"effort":"medium"},"store":False}
    req=Request("https://api.openai.com/v1/responses",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urlopen(req,timeout=90) as r: data=json.load(r)
    out="".join(p.get("text","") for o in data.get("output",[]) if o.get("type")=="message" for p in o.get("content",[]) if p.get("type")=="output_text").strip()
    if out.startswith("```"): out="\n".join(out.splitlines()[1:-1])
    task=json.loads(out)
    if not isinstance(task.get("steps"),list): raise ValueError("planner returned invalid task")
    return task

if __name__=="__main__":
    objective=os.getenv("BROWSER_OBJECTIVE") or " ".join(sys.argv[1:])
    if not objective: raise SystemExit("objective is required")
    print(json.dumps(plan(objective),ensure_ascii=False))
