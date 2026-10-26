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
        text = str(result.get("recommendation") or "")[:600]
        if not text:
            print("github_agents: model returned empty recommendation", file=sys.stderr)
        return text or None
    except WorkerError as exc:
        # Log why the model step failed (research-learner #24 on 2026-10-17 ended
        # model_unavailable for every domain with no trace while provider_health was ok).
        print(f"github_agents: model_unavailable: {type(exc).__name__}: {str(exc)[:1200]}", file=sys.stderr)
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


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Fail closed on repeated JSON keys at any nesting depth."""
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _strict_json_loads(raw: str) -> Any:
    """No last-key-wins or NaN/Infinity in research identity evidence."""
    return json.loads(raw, object_pairs_hook=_reject_duplicate_pairs,
                      parse_constant=_reject_nonfinite_constant)


def _canonical_learning_rows(doc: Any) -> list[dict[str, Any]] | None:
    """Fail closed if the canonical ledger has lost its schema or learning identities."""
    if not isinstance(doc, dict) or type(doc.get("schema_version")) is not int or doc["schema_version"] != 1:
        return None
    rows = doc.get("learnings")
    if not isinstance(rows, list):
        return None
    seen: set[str] = set()
    for row in rows:
        if (not isinstance(row, dict)
                or not isinstance(row.get("learning_id"), str) or not row["learning_id"]
                or not isinstance(row.get("title"), str) or not row["title"]
                or not isinstance(row.get("source_ids"), list) or not row["source_ids"]
                or any(not isinstance(ref, str) or not ref for ref in row["source_ids"])
                or len(row["source_ids"]) != len(set(row["source_ids"]))
                or row["learning_id"] in seen):
            return None
        seen.add(row["learning_id"])
    return rows


def _known_learning_titles(root: Path) -> set[str] | None:
    """Return None when canonical history is unreadable; never treat that as an empty ledger."""
    try:
        ledger = _strict_json_loads((root / "knowledge" / "learning_ledger.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    rows = _canonical_learning_rows(ledger)
    return None if rows is None else {row["title"] for row in rows}


def _validated_staged_rows(doc: Any) -> tuple[set[str], list[tuple[str, str, list[str]]]] | None:
    """Reject the entire staged document if any identity, reference or duplicate is invalid."""
    if (not isinstance(doc, dict) or doc.get("schema_version") != 1
            or not isinstance(doc.get("sources"), list) or not doc["sources"]
            or not isinstance(doc.get("learnings"), list) or not doc["learnings"]):
        return None
    valid_sources: set[str] = set()
    canonicals: set[str] = set()
    for source in doc["sources"]:
        if not isinstance(source, dict) or not isinstance(source.get("canonical"), str):
            return None
        try:
            canonical = canonicalize(source["canonical"])
            sid = source_id(canonical)
        except (ValueError, RuntimeError, TypeError):
            return None
        if source.get("source_id") != sid or sid in valid_sources or canonical in canonicals:
            return None
        valid_sources.add(sid)
        canonicals.add(canonical)
    valid_learnings: list[tuple[str, str, list[str]]] = []
    seen_learning_ids: set[str] = set()
    for learning in doc["learnings"]:
        if not isinstance(learning, dict):
            return None
        domain, claim, refs = learning.get("domain"), learning.get("claim"), learning.get("source_ids")
        title, lid = learning.get("title"), learning.get("learning_id")
        if (not isinstance(domain, str) or not domain
                or not isinstance(claim, str) or not claim
                or not isinstance(title, str) or not title
                or not isinstance(refs, list) or not refs
                or any(not isinstance(ref, str) or ref not in valid_sources for ref in refs)
                or len(refs) != len(set(refs))):
            return None
        try:
            expected_id = learning_id(domain, claim)
        except (ValueError, RuntimeError, TypeError):
            return None
        if lid != expected_id or lid in seen_learning_ids:
            return None
        seen_learning_ids.add(lid)
        valid_learnings.append((title, lid, refs))
    return valid_sources, valid_learnings


def _staged_learning_titles(root: Path) -> set[str]:
    """Deduplicate only fully valid, still-pending intake files; never trust partial documents."""
    titles: set[str] = set()
    folder = root / "intake" / "promotions"
    if not folder.is_dir() or folder.is_symlink():
        return titles
    for path in folder.glob("*.json"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            doc = _strict_json_loads(path.read_text(encoding="utf-8"))
            validated = _validated_staged_rows(doc)
            if validated is not None:
                titles.update(title for title, _, _ in validated[1])
        except (OSError, ValueError, AttributeError, TypeError):
            continue
    return titles

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
        known = _known_learning_titles(root)
        if known is None:
            entry["status"] = "ledger_unavailable"
            report["domains"][key] = entry
            continue
        title = f"{spec['name']}: {_CLEAN.sub(' ', item['title'])[:200]}"[:180]
        if title in known:
            entry["status"] = "already_in_ledger"
            report["domains"][key] = entry
            continue
        if title in _staged_learning_titles(root):
            entry["status"] = "already_staged"
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
        # Exclusive creation prevents an hourly rerun from overwriting a
        # different, still-unreviewed candidate under the date-based filename.
        target = safe_output_path(root, rel)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.parent.resolve().is_relative_to(root.resolve()):
                raise ValueError("staging directory escapes repository")
            with target.open("x", encoding="utf-8") as out:
                out.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
            if json.loads(target.read_text(encoding="utf-8")) != doc:
                raise ValueError("staging read-back mismatch")
        except FileExistsError:
            entry.update(status="staging_collision", path=rel)
            report["domains"][key] = entry
            continue
        except (OSError, ValueError) as exc:
            entry.update(status=f"staging_write_failed:{type(exc).__name__}", path=rel)
            report["domains"][key] = entry
            continue
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
    # The REST endpoint is paginated. A successful first-page request cannot
    # prove that older runs or additional workflows are healthy.
    runs = data.get("workflow_runs")
    if not isinstance(runs, list):
        return "okunamadı (workflow_runs eksik)"
    latest: dict[str, str] = {}
    for run in runs:
        if not isinstance(run, dict):
            return "okunamadı (geçersiz workflow run)"
        if run.get("status") == "completed":
            latest.setdefault(run.get("name") or "?", run.get("conclusion") or "?")
    bad = sorted(n for n, conclusion in latest.items()
                 if conclusion not in ("success", "skipped", "neutral"))
    total = data.get("total_count")
    total_known = type(total) is int and total >= len(runs)
    complete = total_known and total == len(runs)
    coverage = (f"ilk {len(runs)} / {total} koşu" if total_known
                else f"ilk {len(runs)} koşu (toplam bilinmiyor)")
    status = "tam tarama" if complete else "KISMİ örnek; tüm CI yeşil doğrulanmadı"
    return (f"{status} ({coverage}); {len(latest)} workflow; "
            f"örnekte başarısız: {', '.join(bad) or 'yok'}")


def _valid_staged_identity(doc: Any, sid: Any, lid: Any) -> bool:
    """All staged rows must be valid before one expected source/learning pair is trusted."""
    if not isinstance(sid, str) or not isinstance(lid, str):
        return False
    validated = _validated_staged_rows(doc)
    if validated is None:
        return False
    sources, learnings = validated
    return sid in sources and any(candidate_id == lid and sid in refs
                                  for _, candidate_id, refs in learnings)

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
    # A prior staged candidate may have been deduplicated and removed after review.
    # State is historical; only a current, safely scoped file proves staging.
    domains = learner.get("domains") or {}
    # A candidate can still be present after its learning was promoted.
    # Do not count an already-canonical learning as a fresh staged discovery.
    try:
        ledger_doc = _strict_json_loads((root / "knowledge" / "learning_ledger.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ledger_doc = {}
    ledger_rows = _canonical_learning_rows(ledger_doc)
    ledger_ready = ledger_rows is not None
    canonical_learning_ids = {row["learning_id"] for row in (ledger_rows or [])}
    staged_live = {}
    staged_promoted = {}
    staged_valid = {}
    for k, v in domains.items():
        rel = v.get("path")
        safe_rel = (isinstance(rel, str) and Path(rel).parts[:2] == ("intake", "promotions")
                    and ".." not in Path(rel).parts and Path(rel).suffix == ".json")
        # A file's presence alone does not prove a valid, identity-matched
        # promotion. Reject corrupt JSON, mismatched IDs and symlink escapes.
        valid = False
        if v.get("status") == "staged" and safe_rel:
            try:
                target = (root / rel).resolve(strict=True)
                boundary = (root / "intake" / "promotions").resolve()
                if target.is_relative_to(boundary) and target.is_file():
                    doc = _strict_json_loads(target.read_text(encoding="utf-8"))
                    valid = _valid_staged_identity(doc, v.get("source_id"), v.get("learning_id"))
            except (OSError, ValueError, TypeError, AttributeError):
                pass
        staged_valid[k] = valid
        staged_promoted[k] = valid and ledger_ready and v.get("learning_id") in canonical_learning_ids
        staged_live[k] = valid and ledger_ready and not staged_promoted[k]
    learn_lines = [
        (f"  - {k}: already_in_ledger (staged file retained; not new)" if staged_promoted[k]
         else f"  - {k}: staged → {v['path']}" if staged_live[k]
         else f"  - {k}: staged_unverified (canonical ledger unavailable)"
         if v.get("status") == "staged" and staged_valid[k] and not ledger_ready
         else f"  - {k}: staged_missing (intake read-back failed or deduplicated)"
         if v.get("status") == "staged"
         else f"  - {k}: {v.get('status')}" + (f" → {v['path']}" if v.get("path") else ""))
        for k, v in domains.items()
    ] or [f"  - {learner.get('skipped') or 'henüz çalışmadı'}"]
    history_path = root / "state" / "agents_history.json"
    history = read_json(history_path, [])
    if not isinstance(history, list):
        history = []
    history.append({"at": current.isoformat(), "overdue": len(overdue), "open": len(open_ho),
                    "staged": sum(staged_live.values())})
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
