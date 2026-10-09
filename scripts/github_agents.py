#!/usr/bin/env python3
"""GitHub-hosted agents that run without Grok Bot (scheduled Actions).

Subcommands:
  automation-runner  observe the 4 automations (finance, video+shorts+shopify+
                     gumroad, knowledge, system); dispatch only allowlisted
                     read-only/test workflows; record run IDs and conclusions
                     in state/automation_runner.json.
  research-learner   per domain fetch one keyless primary source (RSS/Atom),
                     build a promotion JSON (schema_version 1, real source_ids,
                     provenance unverified), validate it against a scratch copy
                     of the catalog+ledger, and stage it in intake/promotions/
                     for review (never knowledge/promotions directly).
  reporter           write a short Turkish hourly + daily report to
                     messages/agents-report-latest.md and messages/chatgpt-to-read.md.

Model calls use the failover chain gemini -> deepseek -> claude -> openai;
with no provider key the model step is skipped cleanly (exit 0).
Agent output is only ever written under state/, messages/ and intake/; never
.github/, never PayoutLens, never secrets.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import handoff  # noqa: E402
from scripts.backup_supervisor import supervisor_adapter  # noqa: E402
from scripts.knowledge_bridge import canonicalize, source_id  # noqa: E402
from scripts.learning_bridge import learning_id  # noqa: E402
from scripts.worker_adapters import WorkerError  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
TRT = timezone(timedelta(hours=3))
USER_AGENT = "cerniva-ai-shared-workspace-research-learner/1.0 (github actions)"
ALLOWED_OUTPUT_PREFIXES = ("state/", "messages/", "intake/")

# Four automations -> workflows observed; ``dispatch`` lists only read-only /
# test workflows that are safe to start. Publishing/upload/payment workflows
# are observe-only (dry run).
AUTOMATIONS: dict[str, dict[str, list[str]]] = {
    "finance": {"observe": ["plan-learnings-check.yml"], "dispatch": ["plan-learnings-check.yml"]},
    "video_shorts_shopify_gumroad": {
        "observe": ["shorts-free-build.yml", "shorts-free-render.yml", "youtube-upload.yml",
                    "tinyfish-youtube-analytics.yml", "shorts-render-tests.yml"],
        "dispatch": [],
    },
    "knowledge": {"observe": ["knowledge-promote.yml"], "dispatch": []},
    "system": {"observe": ["worker-orchestration-tests.yml", "handoff-audit.yml", "desk-notify.yml"],
               "dispatch": ["worker-orchestration-tests.yml"]},
}

# Keyless primary feeds per domain (official publishers).
RESEARCH_SOURCES: dict[str, dict[str, str]] = {
    "finance": {"url": "https://www.federalreserve.gov/feeds/press_all.xml",
                "name": "Federal Reserve Board press releases RSS", "plan": "finance",
                "domain": "finance-news"},
    "video_shopify": {"url": "https://shopify.dev/changelog/feed.xml",
                      "name": "Shopify developer changelog feed", "plan": "video_shopify",
                      "domain": "commerce-platform"},
    "system": {"url": "https://github.blog/changelog/feed/",
               "name": "GitHub changelog feed", "plan": "system", "domain": "github-platform"},
}


def now_utc() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def safe_output_path(root: Path, rel: str) -> Path:
    rel = rel.replace("\\", "/")
    if ".." in rel.split("/") or not rel.startswith(ALLOWED_OUTPUT_PREFIXES) or "payoutlens" in rel.lower():
        raise ValueError(f"agent output path not allowed: {rel}")
    return root / rel


def write_json(root: Path, rel: str, data: Any) -> None:
    path = safe_output_path(root, rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


class GitHub:
    def __init__(self, repo: str | None, token: str | None, http: Callable | None = None):
        self.repo, self.token, self.http = repo, token, http

    @property
    def available(self) -> bool:
        return bool(self.repo and self.token)

    def _call(self, method: str, path: str, body: dict | None = None) -> Any:
        url = f"https://api.github.com/repos/{self.repo}{path}"
        if self.http is not None:
            return self.http(method, url, body)
        data = json.dumps(body).encode() if body is not None else None
        req = Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"})
        with urlopen(req, timeout=20) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}

    def latest_run(self, workflow: str) -> dict[str, Any] | None:
        data = self._call("GET", f"/actions/workflows/{workflow}/runs?branch=main&per_page=1")
        runs = data.get("workflow_runs") or []
        if not runs:
            return None
        r = runs[0]
        return {"id": r.get("id"), "status": r.get("status"), "conclusion": r.get("conclusion"),
                "created_at": r.get("created_at"), "event": r.get("event")}

    def dispatch(self, workflow: str) -> None:
        self._call("POST", f"/actions/workflows/{workflow}/dispatches", {"ref": "main"})


def _summarize(adapter, objective: str) -> str | None:
    if adapter is None:
        return None
    try:
        result = adapter.run({"id": "github-agents-summary", "project": "workspace",
                              "objective": objective, "evidence_requirements": []})
        return str(result.get("recommendation") or "")[:600] or None
    except WorkerError:
        return None


def automation_runner(*, root: Path = ROOT, gh: GitHub, adapter=None, dispatch: bool = True) -> dict[str, Any]:
    report: dict[str, Any] = {"generated_at": now_utc().isoformat(), "github_api": gh.available,
                              "automations": {}}
    for name, spec in AUTOMATIONS.items():
        entry: dict[str, Any] = {"workflows": {}, "dispatched": [], "mode": "dispatch+observe" if spec["dispatch"] else "dry-run"}
        for wf in spec["observe"]:
            if not gh.available:
                entry["workflows"][wf] = {"error": "no_github_api"}
                continue
            try:
                entry["workflows"][wf] = gh.latest_run(wf) or {"status": "never_run"}
            except Exception as exc:
                entry["workflows"][wf] = {"error": type(exc).__name__}
        if dispatch and gh.available:
            for wf in spec["dispatch"]:
                try:
                    gh.dispatch(wf)
                    entry["dispatched"].append(wf)
                except Exception as exc:
                    entry.setdefault("dispatch_errors", {})[wf] = type(exc).__name__
        if name == "finance":
            entry["note"] = "Finans runner workflow'u repoda yok; yalnızca plan-learnings-check gözlenir."
        report["automations"][name] = entry
    report["model_summary"] = _summarize(adapter, "Summarize in Turkish, max 3 sentences, which automations look "
                                         "unhealthy: " + json.dumps(report["automations"], ensure_ascii=False)[:6000])
    write_json(root, "state/automation_runner.json", report)
    return report


def parse_feed(xml_text: str) -> dict[str, str] | None:
    try:
        tree = ET.fromstring(xml_text)
    except ET.ParseError:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    item = tree.find("./channel/item")
    if item is not None:
        return {"title": (item.findtext("title") or "").strip(), "link": (item.findtext("link") or "").strip(),
                "date": (item.findtext("pubDate") or "").strip()}
    entry = tree.find("a:entry", ns)
    if entry is not None:
        link = entry.find("a:link", ns)
        return {"title": (entry.findtext("a:title", default="", namespaces=ns) or "").strip(),
                "link": (link.get("href") if link is not None else "") or "",
                "date": (entry.findtext("a:updated", default="", namespaces=ns) or "").strip()}
    return None


def _default_fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=20) as resp:
        return resp.read(2_000_000).decode("utf-8", errors="replace")


_CLEAN = re.compile(r"\s+")


def build_promotion(domain_key: str, item: dict[str, str], fetched_at: str, decision: str) -> dict[str, Any]:
    spec = RESEARCH_SOURCES[domain_key]
    canonical = canonicalize(spec["url"])
    sid = source_id(canonical)
    title = _CLEAN.sub(" ", item["title"])[:200]
    claim = (f"{spec['name']} fetched {fetched_at[:10]} lists as newest item: \"{title}\""
             + (f" ({item['date']})" if item.get("date") else "") + ". Not independently verified.")
    domain = spec["domain"]
    return {
        "schema_version": 1,
        "sources": [{
            "source_id": sid, "source_name": spec["name"], "canonical": canonical, "category": domain,
            "purpose": f"Keyless primary feed for {spec['plan']} research-learner agent",
            "evidence_tier": "primary", "access_status": "verified-public",
            "cost_quota": "free public feed; no API key", "reliability_limits":
            "Feed headline only; item body not read by the agent.", "discovered_at": fetched_at,
            "provenance": "unverified",
        }],
        "learnings": [{
            "learning_id": learning_id(domain, claim), "title": f"{spec['name']}: {title}"[:180],
            "domain": domain, "claim": claim, "evidence_status": "unverified", "decision": decision,
            "outcome": "pending", "next_measurement": "Reviewer opens the item link and confirms relevance before promotion.",
            "learned_at": fetched_at, "provenance": "unverified", "source_ids": [sid],
            "plan_tags": [spec["plan"]], "failure_history": [], "fallback_history": [],
        }],
    }


def validate_promotion(root: Path, doc: dict[str, Any]) -> None:
    from scripts.knowledge_promote import _apply_batch
    with tempfile.TemporaryDirectory(prefix="research-learner-") as scratch:
        work = Path(scratch)
        promos = work / "promotions"
        promos.mkdir()
        for name in ("source_catalog.json", "learning_ledger.json"):
            src = root / "knowledge" / name
            if src.exists():
                shutil.copyfile(src, work / name)
        (promos / "candidate.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        _apply_batch(promos, work / "source_catalog.json", work / "learning_ledger.json")


def research_learner(*, root: Path = ROOT, adapter=None, fetch: Callable[[str], str] = _default_fetch) -> dict[str, Any]:
    report: dict[str, Any] = {"generated_at": now_utc().isoformat(), "provider_available": adapter is not None,
                              "domains": {}}
    if adapter is None:
        report["skipped"] = "no provider key"
        write_json(root, "state/research_learner.json", report)
        return report
    stamp = now_utc()
    for key, spec in RESEARCH_SOURCES.items():
        entry: dict[str, Any] = {"source": spec["url"]}
        try:
            item = parse_feed(fetch(spec["url"]))
        except Exception as exc:
            entry["status"] = f"fetch_error:{type(exc).__name__}"
            report["domains"][key] = entry
            continue
        if not item or not item.get("title"):
            entry["status"] = "no_item"
            report["domains"][key] = entry
            continue
        decision = _summarize(adapter, f"In one English sentence, what should the '{spec['plan']}' plan do about "
                              f"this primary-source headline (review only, no action): {item['title']}")
        if not decision:
            entry["status"] = "model_unavailable"
            report["domains"][key] = entry
            continue
        doc = build_promotion(key, item, stamp.isoformat(), "REVIEW_ONLY: " + decision)
        rel = f"intake/promotions/{stamp.strftime('%Y-%m-%d')}-research-learner-{key}.json"
        try:
            validate_promotion(root, doc)
        except Exception as exc:
            entry["status"] = f"invalid:{type(exc).__name__}"
            report["domains"][key] = entry
            continue
        write_json(root, rel, doc)
        entry.update(status="staged", path=rel, learning_id=doc["learnings"][0]["learning_id"],
                     source_id=doc["sources"][0]["source_id"])
        report["domains"][key] = entry
    write_json(root, "state/research_learner.json", report)
    return report


def _ci_line(gh: GitHub) -> str:
    if not gh.available:
        return "okunamadı (token yok)"
    try:
        data = gh._call("GET", "/actions/runs?branch=main&per_page=30")
    except Exception as exc:
        return f"okunamadı ({type(exc).__name__})"
    latest: dict[str, str] = {}
    for r in data.get("workflow_runs") or []:
        if r.get("status") == "completed":
            latest.setdefault(r.get("name") or "?", r.get("conclusion") or "?")
    bad = sorted(n for n, c in latest.items() if c not in ("success", "skipped", "neutral"))
    return f"{len(latest)} workflow; başarısız: {', '.join(bad) or 'yok'}"


def reporter(*, root: Path = ROOT, gh: GitHub, now: datetime | None = None) -> str:
    current = (now or now_utc()).astimezone(UTC)
    runner = read_json(root / "state" / "automation_runner.json", {})
    learner = read_json(root / "state" / "research_learner.json", {})
    try:
        hdata = handoff.load(root / "state" / "handoffs.json")
        open_ho = [i["id"] for i in hdata["items"] if i["status"] in ("open", "claimed")]
        overdue = [i["id"] for i in handoff.overdue(hdata, at=current)]
    except Exception:
        open_ho, overdue = [], []
    auto_lines = []
    for name, entry in (runner.get("automations") or {}).items():
        runs = []
        for wf, r in (entry.get("workflows") or {}).items():
            runs.append(f"{wf.removesuffix('.yml')}={r.get('conclusion') or r.get('status') or r.get('error')}"
                        + (f"#{r['id']}" if r.get("id") else ""))
        auto_lines.append(f"  - {name}: {', '.join(runs) or 'veri yok'}"
                          + (f"; tetiklenen: {', '.join(entry['dispatched'])}" if entry.get("dispatched") else ""))
    learn_lines = [f"  - {k}: {v.get('status')}" + (f" → {v['path']}" if v.get("path") else "")
                   for k, v in (learner.get("domains") or {}).items()] or [f"  - {learner.get('skipped') or 'henüz çalışmadı'}"]
    history_path = root / "state" / "agents_history.json"
    history = read_json(history_path, [])
    if not isinstance(history, list):
        history = []
    history.append({"at": current.isoformat(), "overdue": len(overdue), "open": len(open_ho),
                    "staged": sum(1 for v in (learner.get("domains") or {}).values() if v.get("status") == "staged")})
    cutoff = current - timedelta(hours=24)
    history = [h for h in history if datetime.fromisoformat(h["at"]) >= cutoff][-48:]
    write_json(root, "state/agents_history.json", history)
    trt = current.astimezone(TRT).strftime("%Y-%m-%d %H:%M")
    text = "\n".join([
        "# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur",
        "",
        f"Zaman: {trt} TRT",
        "",
        "## Saatlik",
        f"- Açık/claimed handoff: {', '.join(open_ho) or 'yok'}",
        f"- Gecikmiş (>2 sa): {', '.join(overdue) or 'yok'}",
        f"- CI (main): {_ci_line(gh)}",
        "- Otomasyonlar (automation-runner):",
        *(auto_lines or ["  - henüz çalışmadı"]),
        "- Araştırma (research-learner, inceleme için intake/promotions/):",
        *learn_lines,
        "",
        "## Günlük (son 24 sa)",
        f"- Rapor sayısı: {len(history)}; en yüksek gecikmiş: {max((h['overdue'] for h in history), default=0)}; "
        f"aşamalanan promotion: {sum(h['staged'] for h in history)}",
        "",
        "Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. "
        "Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).",
        "",
    ])
    for rel in ("messages/agents-report-latest.md", "messages/chatgpt-to-read.md"):
        path = safe_output_path(root, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text


def main(argv=None, env: Mapping[str, str] | None = None) -> int:
    values = os.environ if env is None else env
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("agent", choices=["automation-runner", "research-learner", "reporter"])
    p.add_argument("--no-dispatch", action="store_true")
    args = p.parse_args(argv)
    gh = GitHub(values.get("GITHUB_REPOSITORY"), values.get("GITHUB_TOKEN"))
    if args.agent == "automation-runner":
        out = automation_runner(gh=gh, adapter=supervisor_adapter(env=values), dispatch=not args.no_dispatch)
    elif args.agent == "research-learner":
        out = research_learner(adapter=supervisor_adapter(env=values))
    else:
        out = {"written": ["messages/agents-report-latest.md", "messages/chatgpt-to-read.md"],
               "chars": len(reporter(gh=gh))}
    print(json.dumps(out, ensure_ascii=False)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
