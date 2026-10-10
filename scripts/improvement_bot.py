#!/usr/bin/env python3
"""Weekly improvement-bot: rule-based bottleneck report + one speed-up job for team-worker.

Inputs (read-only): state/provider_health.json (current + git history of last 7 days),
GitHub Actions runs of the last 7 days, state/handoffs.json, open ``bot/*`` PRs.
Outputs: state/improvement_report.json, messages/improvement-latest.md and (not in dry run)
one new handoff per ISO week + ``repository_dispatch`` ``team-work``.

Idempotent per ISO week: the handoff id is ``HO-IMP-<YYYY>W<WW>-<slug>``; if it already
exists in handoffs.json nothing new is opened or dispatched. Publish/payment workflows are
never used as suggestion targets. Model enrichment is optional (scripts/model_fallback.py);
without a usable provider the rule-based text is kept.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import handoff  # noqa: E402

HEALTH_PATH = ROOT / "state" / "provider_health.json"
REPORT_PATH = ROOT / "state" / "improvement_report.json"
MD_PATH = ROOT / "messages" / "improvement-latest.md"
WINDOW = timedelta(days=7)
OPEN_HANDOFF_LIMIT = timedelta(hours=2)
MIN_RUNS_FOR_FAILURE_RATE = 3
DISPATCH_TYPE = "team-work"
SOURCE = "improvement-bot"
HANDOFF_FROM, HANDOFF_TO = "grok", "auditor"
DOWN_STATUSES = ("no_key", "billing", "quota")

# Publish / payment surfaces are never suggestion targets.
DENYLIST_PATTERNS = (
    re.compile(r"youtube[-_ ]upload", re.I),
    re.compile(r"shorts[-_ ]free[-_ ](render|publish)", re.I),
    re.compile(r"(^|/)meta[-_ ]", re.I),
    re.compile(r"publish|release|deploy", re.I),
    re.compile(r"shopify|gumroad|whop|payment|payout|billing", re.I),
)


def is_denylisted(*names: str) -> bool:
    return any(p.search(n or "") for n in names for p in DENYLIST_PATTERNS)


def redact(text: Any) -> str:
    text = str(text)
    for name, value in os.environ.items():
        if re.search(r"KEY|TOKEN|SECRET|PASSWORD", name) and value and len(value) >= 6:
            text = text.replace(value, "***")
    return re.sub(r"(xai-|sk-|AIza|ghp_|ghs_|github_pat_)[A-Za-z0-9_-]{8,}", r"\1***", text)


def log(event: str, **fields: Any) -> None:
    print(redact(json.dumps({"improvement_bot": event, **fields}, ensure_ascii=False)), flush=True)


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def week_key(at: datetime) -> str:
    y, w, _ = at.isocalendar()
    return f"{y}W{w:02d}"


# ------------------------------------------------------------------ GitHub ---
class GitHubAPI:
    def __init__(self, repo: str, token: str, base: str = "https://api.github.com"):
        self.repo, self.token, self.base = repo, token, base

    def _call(self, method: str, path: str, body: dict | None = None) -> Any:
        url = path if path.startswith("http") else f"{self.base}/repos/{self.repo}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "improvement-bot"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        return json.loads(raw) if raw else {}

    def workflow_runs(self, since: datetime, max_pages: int = 10) -> list[dict]:
        out: list[dict] = []
        q = urllib.parse.quote(f">={since.date().isoformat()}")
        for page in range(1, max_pages + 1):
            res = self._call("GET", f"/actions/runs?per_page=100&page={page}&created={q}")
            runs = res.get("workflow_runs") or []
            out.extend(runs)
            if len(runs) < 100:
                break
        return out

    def open_pulls(self) -> list[dict]:
        return self._call("GET", "/pulls?state=open&per_page=100") or []

    def repository_dispatch(self, event_type: str, client_payload: dict) -> None:
        self._call("POST", "/dispatches", {"event_type": event_type, "client_payload": client_payload})


# ------------------------------------------------------------------ inputs ---
def provider_history_from_git(path: Path = HEALTH_PATH, since: datetime | None = None) -> list[dict]:
    """Snapshots of provider_health.json committed in the window (oldest first). Read-only."""
    since = since or datetime.now(timezone.utc) - WINDOW
    rel = path.relative_to(ROOT).as_posix()
    try:
        shas = subprocess.run(["git", "log", f"--since={since.isoformat()}", "--format=%H", "--", rel],
                              cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    except Exception:
        shas = []
    snaps = []
    for sha in reversed(shas[:500]):
        try:
            raw = subprocess.run(["git", "show", f"{sha}:{rel}"], cwd=ROOT, capture_output=True,
                                 text=True, check=True).stdout
            snaps.append(json.loads(raw))
        except Exception:
            continue
    return snaps


def provider_downtime(snapshots: list[dict], now: datetime) -> dict[str, dict[str, float]]:
    """Seconds each provider spent in no_key/billing/quota; a snapshot holds until the next one."""
    snaps = sorted((s for s in snapshots if parse_ts(s.get("ts"))), key=lambda s: parse_ts(s["ts"]))
    out: dict[str, dict[str, float]] = {}
    seen: set[str] = set()
    for i, snap in enumerate(snaps):
        if snap["ts"] in seen:
            continue
        seen.add(snap["ts"])
        start = max(parse_ts(snap["ts"]), now - WINDOW)
        end = parse_ts(snaps[i + 1]["ts"]) if i + 1 < len(snaps) else now
        span = max(0.0, (min(end, now) - start).total_seconds())
        for p in snap.get("providers") or []:
            st = p.get("status")
            if st in DOWN_STATUSES and p.get("name"):
                bucket = out.setdefault(p["name"], {s: 0.0 for s in DOWN_STATUSES})
                bucket[st] += span
    return out


def workflow_stats(runs: Iterable[dict], now: datetime) -> list[dict]:
    by: dict[str, dict] = {}
    for r in runs:
        created = parse_ts(r.get("created_at"))
        if created and now - created > WINDOW:
            continue
        name = r.get("name") or r.get("path") or "?"
        s = by.setdefault(name, {"workflow": name, "path": r.get("path", ""), "runs": 0,
                                 "failures": 0, "durations": []})
        if r.get("status") != "completed":
            continue
        s["runs"] += 1
        if r.get("conclusion") in ("failure", "timed_out", "startup_failure"):
            s["failures"] += 1
        a, b = parse_ts(r.get("run_started_at") or r.get("created_at")), parse_ts(r.get("updated_at"))
        if a and b and b >= a:
            s["durations"].append((b - a).total_seconds())
    out = []
    for s in by.values():
        d = s.pop("durations")
        s["median_s"] = round(statistics.median(d), 1) if d else 0.0
        s["max_s"] = round(max(d), 1) if d else 0.0
        s["failure_rate"] = round(s["failures"] / s["runs"], 3) if s["runs"] else 0.0
        out.append(s)
    return out


def handoff_findings(data: dict, now: datetime) -> dict[str, list[dict]]:
    yap, long_open = [], []
    for i in data.get("items", []):
        text = " ".join([i.get("task", ""), i.get("reason_cannot_do", ""), i.get("evidence", ""),
                         *[str(n) for n in i.get("notes") or []]])
        if "YAPAMADIM" in text.upper():
            yap.append({"id": i["id"], "to": i["to"], "status": i["status"]})
        created = parse_ts(i.get("created_at"))
        if i.get("status") in ("open", "claimed") and created and now - created > OPEN_HANDOFF_LIMIT:
            long_open.append({"id": i["id"], "to": i["to"], "status": i["status"],
                              "age_h": round((now - created).total_seconds() / 3600, 1),
                              "task": i.get("task", "")[:160]})
    long_open.sort(key=lambda x: -x["age_h"])
    return {"yapamadim": yap, "long_open": long_open}


def bot_prs(pulls: Iterable[dict], now: datetime) -> list[dict]:
    out = []
    for p in pulls:
        ref = ((p.get("head") or {}).get("ref")) or ""
        created = parse_ts(p.get("created_at"))
        if ref.startswith("bot/") and created:
            out.append({"number": p.get("number"), "branch": ref, "url": p.get("html_url"),
                        "wait_h": round((now - created).total_seconds() / 3600, 1)})
    out.sort(key=lambda x: -x["wait_h"])
    return out


# ------------------------------------------------------------------- rules ---
def bottlenecks(wf: list[dict], down: dict[str, dict[str, float]], ho: dict, prs: list[dict]) -> dict:
    timed = [w for w in wf if w["runs"]]
    slowest = sorted(timed, key=lambda w: (-w["median_s"], w["workflow"]))[:3]
    failing = sorted([w for w in timed if w["runs"] >= MIN_RUNS_FOR_FAILURE_RATE and w["failures"]],
                     key=lambda w: (-w["failure_rate"], -w["failures"], w["workflow"]))
    providers = sorted(({"provider": k, "down_h": round(sum(v.values()) / 3600, 1),
                         **{f"{s}_h": round(v[s] / 3600, 1) for s in DOWN_STATUSES}} for k, v in down.items()),
                       key=lambda x: (-x["down_h"], x["provider"]))
    return {
        "slowest_workflows": slowest,
        "most_failing_workflow": failing[0] if failing else None,
        "longest_open_handoff": ho["long_open"][0] if ho["long_open"] else None,
        "most_down_provider": providers[0] if providers else None,
        "providers_down": providers,
        "longest_waiting_bot_pr": prs[0] if prs else None,
        "yapamadim_count": len(ho["yapamadim"]),
    }


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "x"


def suggestions(b: dict) -> list[dict]:
    """Rule-based speed-up suggestions, best first. Publish/payment targets are excluded."""
    out: list[dict] = []
    for w in b["slowest_workflows"]:
        if is_denylisted(w["workflow"], w["path"]):
            continue
        out.append({"key": f"slow-{slug(w['workflow'])}", "kind": "speedup", "target": w["path"] or w["workflow"],
                    "text": (f"'{w['workflow']}' medyan {w['median_s']:.0f} sn ({w['runs']} kosu). "
                             "Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, "
                             "bagimsiz test adimlarini paralel job'a bol.")})
    f = b["most_failing_workflow"]
    if f and not is_denylisted(f["workflow"], f["path"]):
        out.append({"key": f"fail-{slug(f['workflow'])}", "kind": "reliability", "target": f["path"] or f["workflow"],
                    "text": (f"'{f['workflow']}' basarisizlik orani %{f['failure_rate']*100:.0f} "
                             f"({f['failures']}/{f['runs']}). Son kirik kosularin logundaki ilk hatayi duzelt; "
                             "flaky adima retry/timeout ekle.")})
    p = b["most_down_provider"]
    if p:
        out.append({"key": f"provider-{slug(p['provider'])}", "kind": "provider", "target": "config/model_providers.json",
                    "text": (f"'{p['provider']}' 7 gunde {p['down_h']} saat dustu (no_key {p['no_key_h']}, "
                             f"billing {p['billing_h']}, quota {p['quota_h']}). Fallback sirasinda geri al "
                             "veya anahtar/kota duzelene kadar zincirden cikar.")})
    h = b["longest_open_handoff"]
    if h:
        out.append({"key": f"handoff-{slug(h['id'])}", "kind": "handoff", "target": "state/handoffs.json",
                    "text": f"{h['id']} ({h['to']}, {h['status']}) {h['age_h']} saattir acik; sahibine hatirlat veya kapat."})
    pr = b["longest_waiting_bot_pr"]
    if pr:
        out.append({"key": f"pr-{pr['number']}", "kind": "review", "target": pr["branch"],
                    "text": f"bot PR #{pr['number']} ({pr['branch']}) {pr['wait_h']} saattir bekliyor; incele/birlestir/kapat."})
    return [s for s in out if not is_denylisted(s["target"])]


def pick_speedup(sugs: list[dict]) -> dict | None:
    for kind in ("speedup", "reliability", "provider", "handoff", "review"):
        for s in sugs:
            if s["kind"] == kind:
                return s
    return None


def enrich(sug: dict, adapter_factory: Callable[[], Any] | None) -> dict:
    """Optional model enrichment; any failure keeps the rule-based text."""
    sug = dict(sug, enriched_by=None)
    if adapter_factory is None:
        return sug
    try:
        adapter = adapter_factory()
        if adapter is None:
            return sug
        res = adapter.run({"id": f"improvement-{sug['key']}", "project": "ai-shared-workspace",
                           "objective": ("GitHub Actions darbogazi icin tek paragraf somut hizlandirma onerisi yaz. "
                                         f"Bulgu: {sug['text']} Hedef: {sug['target']}"),
                           "evidence_requirements": []})
        rec = str((res or {}).get("recommendation") or "").strip()
        if rec:
            sug["model_text"] = redact(rec)[:800]
            sug["enriched_by"] = (res or {}).get("provider") or getattr(adapter, "provider", "model")
    except Exception as exc:  # CannotDo / WorkerError / network: rule-based path continues
        sug["model_error"] = redact(exc)[:300]
    return sug


def default_adapter_factory():
    from scripts.model_fallback import fallback_adapter
    return fallback_adapter()


# ------------------------------------------------------------------- core ---
def build_report(*, now: datetime, runs: list[dict], pulls: list[dict], handoffs: dict,
                 health_snaps: list[dict], adapter_factory: Callable[[], Any] | None) -> dict:
    wf = workflow_stats(runs, now)
    down = provider_downtime(health_snaps, now)
    ho = handoff_findings(handoffs, now)
    prs = bot_prs(pulls, now)
    b = bottlenecks(wf, down, ho, prs)
    sugs = suggestions(b)
    chosen = pick_speedup(sugs)
    if chosen:
        chosen = enrich(chosen, adapter_factory)
    wk = week_key(now)
    return {"schema_version": 1, "generated_at": now.replace(microsecond=0).isoformat(), "week": wk,
            "window_days": WINDOW.days, "inputs": {"workflow_runs": len(runs), "bot_prs": len(prs),
                                                   "health_snapshots": len(health_snaps)},
            "bottlenecks": b, "yapamadim": ho["yapamadim"], "long_open_handoffs": ho["long_open"],
            "bot_prs": prs, "suggestions": sugs, "speedup": chosen, "dispatch": None}


def handoff_id_for(week: str, sug: dict) -> str:
    return f"HO-IMP-{week}-{slug(sug['key'])}"[:80]


def week_already_dispatched(data: dict, week: str) -> str | None:
    prefix = f"HO-IMP-{week}-"
    for i in data.get("items", []):
        if i["id"].startswith(prefix):
            return i["id"]
    return None


def dispatch_payload(hid: str, sug: dict) -> dict:
    task = sug.get("model_text") or sug["text"]
    return {"handoff_id": hid, "task": f"[{sug['target']}] {task}"[:900], "source": SOURCE}


def plan_handoff(report: dict, data: dict, *, dry_run: bool) -> dict:
    """Add (not in dry run) the weekly handoff via scripts/handoff.add; idempotent per week."""
    sug = report.get("speedup")
    if not sug:
        return {"status": "no_suggestion"}
    existing = week_already_dispatched(data, report["week"])
    if existing:
        return {"status": "already_this_week", "handoff_id": existing}
    hid = handoff_id_for(report["week"], sug)
    payload = dispatch_payload(hid, sug)
    if dry_run:
        return {"status": "dry_run", "handoff_id": hid, "payload": payload}
    handoff.add(data, item_id=hid, sender=HANDOFF_FROM, receiver=HANDOFF_TO, task=payload["task"],
                reason="improvement-bot haftalik hizlandirma onerisi; uygulama team-worker'a (repository_dispatch team-work)",
                evidence=f"state/improvement_report.json week={report['week']} key={sug['key']}",
                at=report["generated_at"])
    handoff.validate(data)
    return {"status": "pending", "handoff_id": hid, "payload": payload}


def render_md(r: dict) -> str:
    b = r["bottlenecks"]
    L = [f"# improvement-bot raporu ({r['week']})", "", f"Uretim: {r['generated_at']} | pencere: {r['window_days']} gun | "
         f"kosu: {r['inputs']['workflow_runs']} | bot PR: {r['inputs']['bot_prs']}", "", "## Darbogazlar", ""]
    L.append("**En yavas 3 workflow (medyan):**")
    L += [f"- {w['workflow']}: {w['median_s']:.0f} sn (maks {w['max_s']:.0f}, {w['runs']} kosu)" for w in b["slowest_workflows"]] or ["- veri yok"]
    f = b["most_failing_workflow"]
    L.append(f"- En cok kirilan: {f['workflow']} %{f['failure_rate']*100:.0f} ({f['failures']}/{f['runs']})" if f else "- En cok kirilan: yok")
    h = b["longest_open_handoff"]
    L.append(f"- En uzun acik devir: {h['id']} {h['age_h']} sa ({h['status']}, {h['to']})" if h else "- En uzun acik devir: yok (>2 sa)")
    p = b["most_down_provider"]
    L.append(f"- En cok dusen saglayici: {p['provider']} {p['down_h']} sa" if p else "- En cok dusen saglayici: yok")
    pr = b["longest_waiting_bot_pr"]
    L.append(f"- En uzun bekleyen bot PR: #{pr['number']} {pr['wait_h']} sa" if pr else "- Acik bot/ PR: yok")
    L.append(f"- YAPAMADIM notlu devir: {b['yapamadim_count']}")
    L += ["", "## Oneriler", ""] + [f"- ({s['kind']}) {s['text']}" for s in r["suggestions"]]
    s = r.get("speedup")
    d = r.get("dispatch") or {}
    L += ["", "## Bu haftanin team-worker isi", "",
          f"- {s['key']} -> {d.get('handoff_id', '-')} ({d.get('status', '-')}); model: {s.get('enriched_by') or 'yok (kural tabanli)'}" if s else "- yok"]
    return "\n".join(L) + "\n"


def write_outputs(report: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(render_md(report), encoding="utf-8")


def cmd_analyze(dry_run: bool, api: GitHubAPI, now: datetime, use_model: bool = True) -> dict:
    data = handoff.load()
    health = provider_history_from_git(since=now - WINDOW)
    try:
        health.append(json.loads(HEALTH_PATH.read_text(encoding="utf-8")))
    except Exception:
        pass
    report = build_report(now=now, runs=api.workflow_runs(now - WINDOW), pulls=api.open_pulls(), handoffs=data,
                          health_snaps=health, adapter_factory=default_adapter_factory if use_model else None)
    report["dispatch"] = plan_handoff(report, data, dry_run=dry_run)
    if report["dispatch"]["status"] == "pending":
        handoff.save(data)
    write_outputs(report)
    return report


def cmd_dispatch(api: GitHubAPI) -> dict:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    d = report.get("dispatch") or {}
    if d.get("status") != "pending":
        return {"status": "skip", "reason": d.get("status")}
    if is_denylisted(d["payload"]["task"].split("]")[0]):
        return {"status": "refused_denylist"}
    api.repository_dispatch(DISPATCH_TYPE, d["payload"])
    return {"status": "sent", "handoff_id": d["handoff_id"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["analyze", "dispatch"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-model", action="store_true")
    args = ap.parse_args(argv)
    api = GitHubAPI(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    if args.command == "analyze":
        r = cmd_analyze(args.dry_run, api, datetime.now(timezone.utc), use_model=not args.no_model)
        log("report", week=r["week"], bottlenecks=r["bottlenecks"], dispatch=r["dispatch"])
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write(render_md(r))
    else:
        log("dispatch", **cmd_dispatch(api))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
