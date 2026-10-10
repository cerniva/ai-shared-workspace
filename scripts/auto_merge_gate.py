#!/usr/bin/env python3
"""auto-merge-gate: squash-merge a PR only when every gate passes (fail-closed).

Gates: not draft, same-repo head on bot/ or allowlisted branch, all CI checks
success, auditor (Takipçi) check present+success, no denylisted file changed,
PR body has handoff id (HO-...) and a test/CI evidence line.
Otherwise the PR stays open and a single idempotent comment explains why.

After a GITHUB_TOKEN merge, no push workflow fires on main; so we send
repository_dispatch type `main-merged` with {pr_number, merge_sha, handoff_id}.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "auto_merge.json"
MARKER = "<!-- auto-merge-gate -->"
OK_CONCLUSIONS = {"success", "skipped", "neutral"}


class GitHub:
    def __init__(self, repo: str, token: str, api: str = "https://api.github.com"):
        self.repo, self.token, self.api = repo, token, api.rstrip("/")

    def request(self, method: str, path: str, body: Any = None) -> Any:
        url = path if path.startswith("http") else f"{self.api}/repos/{self.repo}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}

    def paged(self, path: str, key: str | None = None) -> list:
        out, page = [], 1
        sep = "&" if "?" in path else "?"
        while True:
            res = self.request("GET", f"{path}{sep}per_page=100&page={page}")
            items = res.get(key, []) if key else res
            out.extend(items)
            if len(items) < 100:
                return out
            page += 1


def load_config(path: Path = CONFIG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def denied_files(files: list[str], patterns: list[str]) -> list[str]:
    bad = []
    for f in files:
        low = f.lower()
        if any(fnmatch.fnmatch(low, p.lower()) for p in patterns):
            bad.append(f)
    return bad


def evaluate_checks(check_runs: list[dict], statuses: list[dict], cfg: dict) -> tuple[list[str], list[str]]:
    """Return (blocking reasons, pending reasons)."""
    reasons, pending = [], []
    selfs = set(cfg.get("self_check_names", []))
    auditor = cfg["auditor_check_name"]
    seen: dict[str, str] = {}
    for run in check_runs:
        name = run.get("name", "")
        if name in selfs:
            continue
        if run.get("status") != "completed":
            pending.append(f"check `{name}` henüz tamamlanmadı ({run.get('status')})")
            seen.setdefault(name, "pending")
            continue
        concl = run.get("conclusion") or "unknown"
        if seen.get(name) != "success":
            seen[name] = "success" if concl in OK_CONCLUSIONS else concl
        if concl not in OK_CONCLUSIONS:
            reasons.append(f"check `{name}` başarısız ({concl})")
    for st in statuses:
        ctx, state = st.get("context", ""), st.get("state")
        if ctx in selfs:
            continue
        if state == "pending":
            pending.append(f"status `{ctx}` bekliyor")
        elif state != "success":
            reasons.append(f"status `{ctx}` başarısız ({state})")
        seen.setdefault(ctx, "success" if state == "success" else str(state))
    if auditor not in seen:
        reasons.append(f"denetçi check `{auditor}` bulunamadı (fail-closed)")
    elif seen[auditor] != "success":
        (pending if seen[auditor] == "pending" else reasons).append(
            f"denetçi check `{auditor}` success değil ({seen[auditor]})")
    for req in cfg.get("required_checks", []):
        if req not in seen:
            reasons.append(f"required check `{req}` bulunamadı")
    return reasons, pending


def evaluate(gh: GitHub, pr: dict, cfg: dict) -> dict:
    reasons: list[str] = []
    if pr.get("state") != "open":
        return {"merge": False, "reasons": ["PR açık değil"], "pending": [], "skip_comment": True}
    if pr.get("draft"):
        reasons.append("PR draft")
    head = pr["head"]
    ref = head.get("ref", "")
    if (head.get("repo") or {}).get("full_name") != gh.repo:
        reasons.append("head dalı fork/başka repo")
    if not (any(ref.startswith(p) for p in cfg.get("allowed_head_prefixes", []))
            or ref in cfg.get("allowed_head_branches", [])):
        reasons.append(f"head dalı `{ref}` bot/ veya allowlist'te değil")
    body = pr.get("body") or ""
    ho = re.search(cfg["handoff_regex"], body)
    if not ho:
        reasons.append("PR gövdesinde handoff id (HO-...) yok")
    if not re.search(cfg["evidence_regex"], body):
        reasons.append("PR gövdesinde test/CI kanıt satırı yok")
    files = [f["filename"] for f in gh.paged(f"/pulls/{pr['number']}/files")]
    if not files:
        reasons.append("değişen dosya listesi alınamadı/boş")
    for f in denied_files(files, cfg.get("denylist", [])):
        reasons.append(f"denylist dosyası değişmiş: `{f}`")
    sha = head["sha"]
    runs = gh.paged(f"/commits/{sha}/check-runs", key="check_runs")
    statuses = gh.request("GET", f"/commits/{sha}/status").get("statuses", [])
    r2, pending = evaluate_checks(runs, statuses, cfg)
    reasons += r2
    return {"merge": not reasons and not pending, "reasons": reasons, "pending": pending,
            "handoff_id": ho.group(0) if ho else None, "sha": sha}


def upsert_comment(gh: GitHub, number: int, text: str) -> str:
    body = f"{MARKER}\n{text}"
    for c in gh.paged(f"/issues/{number}/comments"):
        if MARKER in (c.get("body") or ""):
            if c.get("body") == body:
                return "unchanged"
            gh.request("PATCH", f"/issues/comments/{c['id']}", {"body": body})
            return "updated"
    gh.request("POST", f"/issues/{number}/comments", {"body": body})
    return "created"


def process_pr(gh: GitHub, number: int, cfg: dict) -> dict:
    pr = gh.request("GET", f"/pulls/{number}")
    res = evaluate(gh, pr, cfg)
    if res.get("skip_comment"):
        return res
    if not res["merge"]:
        lines = ["**auto-merge-gate: merge edilmedi.** PR açık bırakıldı.", ""]
        lines += [f"- ❌ {r}" for r in res["reasons"]]
        lines += [f"- ⏳ {p}" for p in res["pending"]]
        res["comment"] = upsert_comment(gh, number, "\n".join(lines))
        return res
    merged = gh.request("PUT", f"/pulls/{number}/merge", {
        "merge_method": cfg.get("merge_method", "squash"), "sha": res["sha"],
        "commit_title": f"{pr.get('title', '')} (#{number})"})
    merge_sha = merged.get("sha")
    if not merged.get("merged", bool(merge_sha)):
        res["merge"] = False
        res["comment"] = upsert_comment(gh, number, f"**auto-merge-gate:** merge API reddetti: {merged.get('message')}")
        return res
    payload = {"pr_number": number, "merge_sha": merge_sha, "handoff_id": res["handoff_id"]}
    gh.request("POST", "/dispatches", {"event_type": cfg.get("dispatch_event_type", "main-merged"),
                                       "client_payload": payload})
    res.update(merged=True, dispatch=payload)
    return res


def candidate_prs(gh: GitHub, event_name: str, event: dict) -> list[int]:
    if os.environ.get("PR_NUMBER"):
        return [int(os.environ["PR_NUMBER"])]
    if event_name in ("pull_request", "pull_request_target"):
        return [event["pull_request"]["number"]]
    if event_name == "check_suite":
        return [p["number"] for p in event.get("check_suite", {}).get("pull_requests", [])]
    if event_name == "workflow_run":
        nums = [p["number"] for p in event.get("workflow_run", {}).get("pull_requests", [])]
        if nums:
            return nums
    return [p["number"] for p in gh.paged("/pulls?state=open")]


def main() -> int:
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        print("GITHUB_REPOSITORY/GITHUB_TOKEN eksik", file=sys.stderr)
        return 2
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    event = json.loads(Path(event_path).read_text()) if event_path and Path(event_path).exists() else {}
    gh, cfg = GitHub(repo, token), load_config()
    results = {}
    for n in dict.fromkeys(candidate_prs(gh, os.environ.get("GITHUB_EVENT_NAME", ""), event)):
        try:
            results[n] = process_pr(gh, n, cfg)
        except urllib.error.HTTPError as e:
            results[n] = {"merge": False, "error": f"HTTP {e.code}"}
    print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
