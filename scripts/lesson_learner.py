#!/usr/bin/env python3
"""lesson-learner: turn one merged PR into ONE ledger line for knowledge/lessons.md.

Event-driven: pull_request closed+merged on main (human merges),
repository_dispatch ``main-merged`` from auto-merge-gate (GITHUB_TOKEN merges
emit no pull_request/push events; client_payload {pr_number, merge_sha,
handoff_id}), or workflow_dispatch pr_number. After opening the lesson PR it
sends repository_dispatch ``team-pr-opened`` {pr_number, head_sha, handoff_id}
because PRs opened with GITHUB_TOKEN do not trigger CI/reviewer workflows.
LLM drafting goes ONLY through the existing failover helper
``scripts.backup_supervisor.supervisor_adapter`` (same chain/secrets as
automation-runner / research-learner / agents-reporter:
GEMINI_API_KEY, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY).
No key / provider failure / invalid output -> no lesson, no PLACEHOLDER; a
``YAPAMADIM:`` comment is posted on the merged PR and the process exits 0.
Output goes to branch ``bot/lessons-pr-<n>`` + a PR; never pushes to main.
The PR body satisfies auto-merge-gate (config/auto_merge.json): handoff id
``HO-...`` and a ``CI:`` evidence line. Without a source HO id the body says
"handoff: yok" (no HO- token) so the gate leaves the PR open for a human.
Backlog mode (``--backlog``; workflow_run after provider-health or
workflow_dispatch without pr_number): no state file. The backlog is derived
from merged PRs of the last 14 days carrying a ``YAPAMADIM:`` comment and no
lesson yet (ledger / bot/lessons-pr-N branch / open PR / "Ders yazıldı:"
comment); at most 3 per run. No provider key -> nothing happens, exit 0.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
LEDGER_REL = "knowledge/lessons.md"
HANDOFF_RE = re.compile(r"HO-\d{8}-\d{2}")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,60}$")
BANNED = ("placeholder", "todo", "tbd", "lorem ipsum")
BRANCH_PREFIX = "bot/lessons-pr-"
SELF_PREFIXES = (BRANCH_PREFIX, "lessons/")
RUN_URL_RE = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/actions/runs/(\d+)")
BACKLOG_DAYS = 14
BACKLOG_LIMIT = 3
DONE_PREFIX = "Ders yazıldı:"
PROTECTED_WORKFLOWS = ("youtube-upload", "shorts-free-", "meta-", "shopify", "gumroad")


class LedgerLineError(ValueError):
    pass


def extract_handoff_id(*texts: str | None) -> str | None:
    for t in texts:
        m = HANDOFF_RE.search(t or "")
        if m:
            return m.group(0)
    return None


def _clean(field: Any) -> str:
    return re.sub(r"\s+", " ", str(field or "")).replace("|", "/").strip()


def build_ledger_line(slug: str, evidence: str, lesson: str, decision: str, metric: str) -> str:
    """Validate fields and return `- slug | evidence | lesson | decision | metric`."""
    slug = _clean(slug).lower()
    fields = [_clean(evidence), _clean(lesson), _clean(decision), _clean(metric)]
    if not SLUG_RE.match(slug):
        raise LedgerLineError(f"invalid slug: {slug!r}")
    for name, val in zip(("evidence", "lesson", "decision", "metric"), fields):
        if len(val) < 3:
            raise LedgerLineError(f"empty field: {name}")
    for val in [slug, *fields]:
        low = val.lower()
        if any(re.search(rf"\b{re.escape(b)}\b", low) for b in BANNED):
            raise LedgerLineError("banned placeholder text")
    if not re.search(r"(PR #\d+|\b[0-9a-f]{7,40}\b|run \d+)", fields[0]):
        raise LedgerLineError("evidence lacks SHA/PR#/run id")
    return "- " + " | ".join([slug, *fields])


def lesson_branch(pr_number: int) -> str:
    return f"{BRANCH_PREFIX}{int(pr_number)}"


def is_duplicate(ledger_text: str, pr_number: int, merge_sha: str | None,
                 existing_branches: list[str] | None = None, open_pr_heads: list[str] | None = None) -> bool:
    if merge_sha and (merge_sha in ledger_text or merge_sha[:7] in ledger_text):
        return True
    if re.search(rf"PR #{int(pr_number)}(?!\d)", ledger_text):
        return True
    branch = lesson_branch(pr_number)
    return branch in (existing_branches or []) or branch in (open_pr_heads or [])


def should_skip(pr: Mapping[str, Any], changed_files: list[str]) -> str | None:
    """Return a skip reason or None."""
    if not pr.get("merged"):
        return "not merged"
    if (pr.get("base") or {}).get("ref") != "main":
        return "base is not main"
    head = (pr.get("head") or {}).get("ref") or ""
    if head.startswith(SELF_PREFIXES):
        return f"self-loop: {head} branch"
    if changed_files and all(f == LEDGER_REL for f in changed_files):
        return "self-loop: only knowledge/lessons.md"
    return None


def append_to_ledger(text: str, line: str, date: str) -> str:
    """Append line under `## date` (section created at end if missing)."""
    if not line.startswith("- ") or line in text:
        return text
    lines = text.rstrip("\n").split("\n")
    header = f"## {date}"
    if header not in lines:
        return "\n".join(lines) + f"\n\n{header}\n{line}\n"
    idx = lines.index(header)
    end = idx + 1
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    while end > idx + 1 and not lines[end - 1].strip():
        end -= 1
    lines.insert(end, line)
    return "\n".join(lines) + "\n"


def parse_dispatch_payload(payload: Mapping[str, Any] | None) -> int | None:
    """repository_dispatch main-merged client_payload -> pr_number (validated int > 0)."""
    raw = (payload or {}).get("pr_number")
    try:
        n = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def team_pr_opened_payload(pr_number: int, head_sha: str, handoff_id: str | None) -> dict[str, Any]:
    return {"event_type": "team-pr-opened",
            "client_payload": {"pr_number": pr_number, "head_sha": head_sha, "handoff_id": handoff_id}}


def ci_evidence_line(merge_sha: str, checks: dict[str, str], run_urls: list[str]) -> str:
    """`CI:` line for the gate's evidence_regex; reports real conclusions, never invents success."""
    summary = ", ".join(f"{k}={v}" for k, v in sorted(checks.items())[:10]) or "check-run bulunamadı"
    line = f"CI: kaynak merge {merge_sha[:7]} check-run sonuçları: {summary}"
    if run_urls:
        line += " — " + " ".join(sorted(set(run_urls))[:3])
    return line


def lesson_pr_body(pr_number: int, merge_sha: str, handoff_id: str | None, ci_line: str, line: str) -> str:
    ho = handoff_id if handoff_id else "handoff: yok (kaynak PR'da handoff id bulunamadı; gate birleştirmez, insan incelemesi)"
    return (f"Kaynak: PR #{pr_number} ({merge_sha[:7]})\n{ho}\n{ci_line}\n\n"
            f"Ders satırı (knowledge/lessons.md):\n{line}\n")


def _parse_ts(value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def select_backlog(candidates: list[Mapping[str, Any]], ledger_text: str, *, now: datetime,
                   existing_branches: list[str] | None = None, open_pr_heads: list[str] | None = None,
                   days: int = BACKLOG_DAYS, limit: int = BACKLOG_LIMIT) -> list[int]:
    """Pick merged PRs (newest first) with a YAPAMADIM comment and no lesson yet.

    candidate keys: number, merge_sha, merged_at (ISO), head_ref, comments (list[str]).
    """
    picked: list[int] = []
    seen: set[int] = set()
    cutoff = now.timestamp() - days * 86400
    ordered = sorted(candidates, key=lambda c: c.get("merged_at") or "", reverse=True)
    for c in ordered:
        n = int(c.get("number") or 0)
        merged = _parse_ts(c.get("merged_at"))
        if n <= 0 or n in seen or merged is None or merged.timestamp() < cutoff:
            continue
        seen.add(n)
        if (c.get("head_ref") or "").startswith(SELF_PREFIXES):
            continue
        comments = [str(x or "").lstrip() for x in c.get("comments") or []]
        if not any(x.startswith("YAPAMADIM:") for x in comments):
            continue
        if any(x.startswith(DONE_PREFIX) for x in comments):
            continue
        if is_duplicate(ledger_text, n, c.get("merge_sha"), existing_branches, open_pr_heads):
            continue
        picked.append(n)
        if len(picked) >= limit:
            break
    return picked


def build_objective(pr: Mapping[str, Any], files: list[str], checks: dict[str, str], handoff_id: str | None) -> str:
    return (
        "Bu birleşmiş PR'dan TEK, tekrar kullanılabilir, kanıta dayalı bir ders çıkar. Sadece JSON döndür: "
        '{"slug":"kebab-case","lesson":"...","decision":"...","metric":"..."}. Uydurma yapma; placeholder yazma.\n'
        f"PR #{pr.get('number')}: {pr.get('title')}\nHandoff: {handoff_id or '-'}\n"
        f"Body: {(pr.get('body') or '')[:2000]}\nFiles: {', '.join(files[:50])}\n"
        f"Checks@{(pr.get('merge_commit_sha') or '')[:7]}: {json.dumps(checks)}"
    )


def parse_llm(text: str) -> dict[str, str]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise LedgerLineError("no JSON in provider output")
    try:
        data = json.loads(m.group(0))
    except ValueError as exc:
        raise LedgerLineError("invalid JSON in provider output") from exc
    if not isinstance(data, dict):
        raise LedgerLineError("provider output not an object")
    return data


def evidence_for(pr: Mapping[str, Any], checks: dict[str, str], handoff_id: str | None, run_id: str | None) -> str:
    parts = [f"PR #{pr.get('number')}", f"merge {(pr.get('merge_commit_sha') or '')[:7]}"]
    if handoff_id:
        parts.append(handoff_id)
    if checks:
        parts.append("checks: " + ", ".join(f"{k}={v}" for k, v in sorted(checks.items())[:8]))
    if run_id:
        parts.append(f"lesson-learner run {run_id}")
    return "; ".join(parts)


def draft_line(adapter, pr, files, checks, handoff_id, run_id) -> tuple[str | None, str | None]:
    """Return (line, None) or (None, yapamadim_reason)."""
    if adapter is None:
        return None, "LLM sağlayıcı anahtarı yok (GEMINI/DEEPSEEK/ANTHROPIC/OPENAI_API_KEY boş)"
    try:
        result = adapter.run({"id": f"lesson-pr-{pr.get('number')}", "project": "workspace",
                              "objective": build_objective(pr, files, checks, handoff_id),
                              "evidence_requirements": []})
        raw = str((result or {}).get("recommendation") or "")
    except Exception as exc:  # provider chain failure -> YAPAMADIM, never crash
        return None, f"sağlayıcı hatası: {type(exc).__name__}"
    try:
        d = parse_llm(raw)
        return build_ledger_line(d.get("slug", ""), evidence_for(pr, checks, handoff_id, run_id),
                                 d.get("lesson", ""), d.get("decision", ""), d.get("metric", "")), None
    except LedgerLineError as exc:
        return None, f"geçersiz LLM çıktısı: {exc}"


def yapamadim_body(reason: str, pr_number: int) -> str:
    return (f"YAPAMADIM: PR #{pr_number} için ders yazılamadı.\n- sebep: {reason}\n"
            "- denenen: scripts.backup_supervisor.supervisor_adapter failover zinciri\n"
            "- gereken: geçerli sağlayıcı anahtarı / geçerli çıktı; ledger'a PLACEHOLDER yazılmadı.")


class GH:
    def __init__(self, repo: str, token: str, http: Callable | None = None):
        self.repo, self.token, self.http = repo, token, http

    def call(self, method: str, path: str, body: dict | None = None) -> Any:
        url = f"https://api.github.com/repos/{self.repo}{path}"
        if self.http is not None:
            return self.http(method, url, body)
        data = json.dumps(body).encode() if body is not None else None
        req = Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"})
        with urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}


def run(pr_number: int, *, gh: GH, env: Mapping[str, str], root: Path = ROOT, adapter=None,
        git: Callable[[list[str]], None] | None = None, comment_on_fail: bool = True) -> dict[str, Any]:
    pr = gh.call("GET", f"/pulls/{pr_number}")
    files = [f["filename"] for f in gh.call("GET", f"/pulls/{pr_number}/files?per_page=100")]
    reason = should_skip(pr, files)
    if reason:
        return {"status": "skip", "reason": reason}
    sha = pr.get("merge_commit_sha") or ""
    ledger = (root / LEDGER_REL).read_text(encoding="utf-8")
    branches = [b["name"] for b in gh.call("GET", "/branches?per_page=100") or []]
    heads = [p["head"]["ref"] for p in gh.call("GET", "/pulls?state=open&per_page=100") or []]
    if is_duplicate(ledger, pr_number, sha, branches, heads):
        return {"status": "skip", "reason": "duplicate"}
    runs = (gh.call("GET", f"/commits/{sha}/check-runs?per_page=100") or {}).get("check_runs") or []
    checks = {r["name"]: (r.get("conclusion") or r.get("status") or "?") for r in runs}
    run_urls = [m.group(0) for r in runs if (m := RUN_URL_RE.search(r.get("details_url") or r.get("html_url") or ""))]
    hid = extract_handoff_id(pr.get("title"), pr.get("body"), (pr.get("head") or {}).get("ref"),
                             env.get("DISPATCH_HANDOFF_ID"))
    line, why = draft_line(adapter, pr, files, checks, hid, env.get("GITHUB_RUN_ID"))
    if line is None:
        if comment_on_fail:
            gh.call("POST", f"/issues/{pr_number}/comments", {"body": yapamadim_body(why or "?", pr_number)})
        return {"status": "yapamadim", "reason": why}
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (root / LEDGER_REL).write_text(append_to_ledger(ledger, line, date), encoding="utf-8")
    branch = lesson_branch(pr_number)
    g = git or (lambda a: subprocess.run(["git", *a], cwd=root, check=True))
    g(["checkout", "-b", branch])
    g(["add", LEDGER_REL])
    g(["commit", "-m", f"knowledge(lessons): PR #{pr_number} dersi"])
    try:
        g(["push", "origin", f"HEAD:refs/heads/{branch}"])  # non-force: a parallel run's branch wins
    except subprocess.CalledProcessError:
        return {"status": "skip", "reason": f"branch {branch} already pushed by a parallel run"}
    new = gh.call("POST", "/pulls", {"title": f"knowledge(lessons): PR #{pr_number} dersi", "head": branch,
                                     "base": "main", "draft": False,
                                     "body": lesson_pr_body(pr_number, sha, hid, ci_evidence_line(sha, checks, run_urls), line)})
    new_no = new.get("number")
    head_sha = (new.get("head") or {}).get("sha") or ""
    try:
        gh.call("POST", "/dispatches", team_pr_opened_payload(new_no, head_sha, hid))
    except Exception as exc:  # PR exists; dispatch failure must be visible but not fatal
        return {"status": "opened", "pr": new_no, "line": line, "dispatch_error": type(exc).__name__}
    return {"status": "opened", "pr": new_no, "line": line, "dispatched": "team-pr-opened"}


def fetch_backlog_candidates(gh: GH, *, now: datetime, days: int = BACKLOG_DAYS) -> list[dict[str, Any]]:
    cutoff = now.timestamp() - days * 86400
    pulls = gh.call("GET", "/pulls?state=closed&base=main&sort=updated&direction=desc&per_page=100") or []
    out = []
    for p in pulls:
        merged = _parse_ts(p.get("merged_at"))
        if merged is None or merged.timestamp() < cutoff:
            continue
        ref = (p.get("head") or {}).get("ref") or ""
        if ref.startswith(SELF_PREFIXES):
            continue
        comments = gh.call("GET", f"/issues/{p['number']}/comments?per_page=100") or []
        out.append({"number": p["number"], "merge_sha": p.get("merge_commit_sha"), "merged_at": p.get("merged_at"),
                    "head_ref": ref, "comments": [c.get("body") or "" for c in comments]})
    return out


def run_backlog(*, gh: GH, env: Mapping[str, str], root: Path = ROOT, adapter=None,
                git: Callable[[list[str]], None] | None = None, now: datetime | None = None,
                limit: int = BACKLOG_LIMIT) -> dict[str, Any]:
    """Retry YAPAMADIM PRs once a provider is available. No key -> no API calls, exit 0."""
    if adapter is None:
        return {"status": "skip", "reason": "no provider key; backlog untouched"}
    now = now or datetime.now(timezone.utc)
    ledger = (root / LEDGER_REL).read_text(encoding="utf-8")
    branches = [b["name"] for b in gh.call("GET", "/branches?per_page=100") or []]
    heads = [p["head"]["ref"] for p in gh.call("GET", "/pulls?state=open&per_page=100") or []]
    picked = select_backlog(fetch_backlog_candidates(gh, now=now), ledger, now=now,
                            existing_branches=branches, open_pr_heads=heads, limit=limit)
    results = []
    for n in picked:
        if git is None:  # each lesson branch starts from a clean main checkout
            subprocess.run(["git", "checkout", "-q", "-f", "main"], cwd=root, check=True)
        res = run(n, gh=gh, env=env, root=root, adapter=adapter, git=git, comment_on_fail=False)
        results.append({"source": n, **{k: v for k, v in res.items() if k != "line"}})
        if res.get("status") == "yapamadim":
            break  # provider chain failed again: stop, keep quota, no duplicate YAPAMADIM
        if res.get("status") == "opened" and res.get("pr"):
            gh.call("POST", f"/issues/{n}/comments", {"body": f"{DONE_PREFIX} #{res['pr']}"})
    return {"status": "backlog", "picked": picked, "results": results}


def main(argv=None, env: Mapping[str, str] | None = None) -> int:
    values = os.environ if env is None else env
    p = argparse.ArgumentParser(description="lesson-learner")
    p.add_argument("--pr", default="", help="PR number (pull_request / workflow_dispatch)")
    p.add_argument("--dispatch-payload", default="", help="repository_dispatch client_payload JSON")
    p.add_argument("--backlog", action="store_true", help="retry YAPAMADIM PRs (max 3)")
    args = p.parse_args(argv)
    from scripts.backup_supervisor import supervisor_adapter
    gh = GH(values.get("GITHUB_REPOSITORY", ""), values.get("GITHUB_TOKEN", ""))
    if args.backlog and not args.pr:
        print(json.dumps(run_backlog(gh=gh, env=values, adapter=supervisor_adapter(env=values)), ensure_ascii=False))
        return 0
    pr_no = parse_dispatch_payload({"pr_number": args.pr}) if args.pr else None
    if pr_no is None and args.dispatch_payload:
        try:
            pr_no = parse_dispatch_payload(json.loads(args.dispatch_payload))
        except ValueError:
            pr_no = None
    if pr_no is None:
        print(json.dumps({"status": "skip", "reason": "no valid pr_number"}))
        return 0
    if args.dispatch_payload:
        try:
            ho = (json.loads(args.dispatch_payload) or {}).get("handoff_id")
        except (ValueError, AttributeError):
            ho = None
        if ho:
            values = {**values, "DISPATCH_HANDOFF_ID": str(ho)}
    out = run(pr_no, gh=gh, env=values, adapter=supervisor_adapter(env=values))
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
