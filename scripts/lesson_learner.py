#!/usr/bin/env python3
"""lesson-learner: turn one merged PR into ONE ledger line for knowledge/lessons.md.

Event-driven: pull_request closed+merged on main, push to main (GITHUB_TOKEN
auto-merges emit no pull_request event; PR resolved from commit message or
/commits/{sha}/pulls), or workflow_dispatch pr_number.
LLM drafting goes ONLY through the existing failover helper
``scripts.backup_supervisor.supervisor_adapter`` (same chain/secrets as
automation-runner / research-learner / agents-reporter:
GEMINI_API_KEY, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY).
No key / provider failure / invalid output -> no lesson, no PLACEHOLDER; a
``YAPAMADIM:`` comment is posted on the merged PR and the process exits 0.
Output goes to branch ``lessons/pr-<n>`` + a PR; never pushes to main.
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


def is_duplicate(ledger_text: str, pr_number: int, merge_sha: str | None,
                 existing_branches: list[str] | None = None, open_pr_heads: list[str] | None = None) -> bool:
    if merge_sha and (merge_sha in ledger_text or merge_sha[:7] in ledger_text):
        return True
    if re.search(rf"PR #{int(pr_number)}(?!\d)", ledger_text):
        return True
    branch = f"lessons/pr-{int(pr_number)}"
    return branch in (existing_branches or []) or branch in (open_pr_heads or [])


def should_skip(pr: Mapping[str, Any], changed_files: list[str]) -> str | None:
    """Return a skip reason or None."""
    if not pr.get("merged"):
        return "not merged"
    if (pr.get("base") or {}).get("ref") != "main":
        return "base is not main"
    head = (pr.get("head") or {}).get("ref") or ""
    if head.startswith("lessons/"):
        return "self-loop: lessons/ branch"
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


MERGE_MSG_RE = re.compile(r"^Merge pull request #(\d+)\b")
SQUASH_MSG_RE = re.compile(r"\(#(\d+)\)\s*$")


def pr_number_from_commit_message(message: str | None) -> int | None:
    """Merge commit 'Merge pull request #N ...' or squash '... (#N)' on the first line."""
    first = (message or "").split("\n", 1)[0].strip()
    m = MERGE_MSG_RE.match(first) or SQUASH_MSG_RE.search(first)
    return int(m.group(1)) if m else None


def resolve_push_pr(sha: str, message: str | None, gh) -> int | None:
    """Find the merged PR for a push to main: commit message first, then API commit->PR map."""
    n = pr_number_from_commit_message(message)
    if n:
        return n
    try:
        pulls = gh.call("GET", f"/commits/{sha}/pulls") or []
    except Exception:
        return None
    merged = [p for p in pulls if p.get("merged_at") and (p.get("base") or {}).get("ref") == "main"]
    return int(merged[0]["number"]) if merged else None


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
        git: Callable[[list[str]], None] | None = None) -> dict[str, Any]:
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
    hid = extract_handoff_id(pr.get("title"), pr.get("body"), (pr.get("head") or {}).get("ref"))
    line, why = draft_line(adapter, pr, files, checks, hid, env.get("GITHUB_RUN_ID"))
    if line is None:
        gh.call("POST", f"/issues/{pr_number}/comments", {"body": yapamadim_body(why or "?", pr_number)})
        return {"status": "yapamadim", "reason": why}
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (root / LEDGER_REL).write_text(append_to_ledger(ledger, line, date), encoding="utf-8")
    branch = f"lessons/pr-{pr_number}"
    g = git or (lambda a: subprocess.run(["git", *a], cwd=root, check=True))
    g(["checkout", "-b", branch])
    g(["add", LEDGER_REL])
    g(["commit", "-m", f"knowledge(lessons): PR #{pr_number} dersi"])
    try:
        g(["push", "origin", f"HEAD:refs/heads/{branch}"])  # non-force: a parallel run's branch wins
    except subprocess.CalledProcessError:
        return {"status": "skip", "reason": f"branch {branch} already pushed by a parallel run"}
    new = gh.call("POST", "/pulls", {"title": f"knowledge(lessons): PR #{pr_number} dersi", "head": branch,
                                     "base": "main", "body": f"Kaynak: PR #{pr_number} ({sha[:7]}).\n\n{line}"})
    return {"status": "opened", "pr": new.get("number"), "line": line}


def main(argv=None, env: Mapping[str, str] | None = None) -> int:
    values = os.environ if env is None else env
    p = argparse.ArgumentParser(description="lesson-learner")
    p.add_argument("--pr", type=int)
    p.add_argument("--push-sha", help="push event: resolve merged PR from this commit")
    args = p.parse_args(argv)
    from scripts.backup_supervisor import supervisor_adapter
    gh = GH(values.get("GITHUB_REPOSITORY", ""), values.get("GITHUB_TOKEN", ""))
    if args.pr is None:
        n = resolve_push_pr(args.push_sha or "", values.get("HEAD_COMMIT_MESSAGE"), gh) if args.push_sha else None
        if n is None:
            print(json.dumps({"status": "skip", "reason": "no merged PR for push"}))
            return 0
        args.pr = n
    out = run(args.pr, gh=gh, env=values, adapter=supervisor_adapter(env=values))
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
