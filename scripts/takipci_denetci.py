#!/usr/bin/env python3
"""takipci-denetci: rule-based PR/commit auditor (no model, no API keys).

Inspects the files changed by a PR (or a merge commit) via the GitHub API with
GITHUB_TOKEN and emits a JSON verdict {verdict, reasons, warnings}. Rules:
  1. feat/fix title but only docs/outputs/knowledge/*.md/intake changed -> fail
  2. a changed file has a line that is a stub marker as a standalone token at
     line start (see MARKER_RE; optional '# ' comment prefix allowed) or a
     line that starts with the tmp-file paste prefix (see TMP_PREFIX) -> fail
  3. a code file (.py/.yml/.yaml/.js/.ts) shrinks by >80% or to <5 lines -> fail
  4. PR body lacks an HO-... id or a Test:/CI: line -> fail (warn-only for
     human PRs whose head branch is not bot/)
  5. (PR mode) every Actions run referenced in the body (.../actions/runs/<id>,
     'run <id>', '#<id>' with 8+ digits) must exist in this repo with
     conclusion success; head_sha != PR head -> warning
  6. a Test:/CI: line (or the line right after it) mentions failure words -> fail
  7. (PR mode) any completed check run on head_sha (except this auditor) with
     conclusion failure/cancelled/timed_out -> fail
  8. (dispatch mode, team-pr-opened) client_payload.ci_pending=true or any other
     check on head_sha still queued/in_progress -> fail "ci_pending: CI not
     finished" (plain pull_request mode ignores in-progress checks; the gate
     handles those)
When --publish is given the verdict is posted as a check run named exactly
CHECK_NAME on the head SHA (that is what auto-merge-gate reads, see
config/auto_merge.json `auditor_check_name`). Read-only otherwise.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CHECK_NAME = "takipci-denetci"
# Built by concatenation so this file does not trip its own rule.
MARKERS = ("PLACE" + "HOLDER", "INCOMPLETE" + "_PUSH")
TMP_PREFIX = "@" + "/tmp/"
# Line-start stub marker: marker as a standalone token at line start (optional
# '# ' comment prefix allowed), NOT followed by an identifier char or an
# assignment. Catches bot-pasted stub lines without flagging legitimate
# mentions inside regexes/docstrings (e.g. archive_heal.py's sentinel list).
# Built by concatenation so this file does not trip its own rule.
MARKER_RE = re.compile(
    r"^\s*(?:#\s*)?(?:" + "PLACE" + "HOLDER|INCOMPLETE" + r"_PUSH)(?![A-Za-z0-9_])(?!\s*=)",
    re.IGNORECASE,
)
CODE_EXT = (".py", ".yml", ".yaml", ".js", ".ts")
DOC_PREFIXES = ("docs/", "outputs/", "intake/")
HO_RE = re.compile(r"\bHO-[0-9A-Za-z][0-9A-Za-z_-]*")
EVIDENCE_RE = re.compile(r"(?im)^\s*[-*]?\s*(test|tests|ci)\s*:")
FEATFIX_RE = re.compile(r"^\s*(feat|fix)\b", re.I)
RUN_URL_RE = re.compile(r"github\.com/([\w.-]+/[\w.-]+)/actions/runs/(\d+)")
RUN_BARE_RE = re.compile(r"(?i)(?:\brun\s+#?|#)(\d{8,})\b")
EVIDENCE_LINE_RE = re.compile(r"(?i)^\s*[-*]?\s*(test|tests|ci)\s*:")
FAIL_WORD_RE = re.compile(r"(?i)(?<!\b0 )\b(failure|failed|kırmızı)\b")
BAD_CONCLUSIONS = {"failure", "cancelled", "timed_out"}
CI_PENDING_REASON = "ci_pending: CI not finished"
# Never wait on ourselves or on the gate (it runs until we finish).
PENDING_IGNORE = {CHECK_NAME, "auto-merge-gate"}
SHRINK_RATIO = 0.8
MIN_LINES = 5


def is_doc_only_path(path: str) -> bool:
    p = path.lstrip("./")
    if p.startswith(DOC_PREFIXES) or "/intake/" in p or p.startswith("intake"):
        return True
    return p.startswith("knowledge/") and p.lower().endswith(".md")


def is_code(path: str) -> bool:
    return path.lower().endswith(CODE_EXT)


def line_count(text: str | None) -> int:
    return len(text.splitlines()) if text else 0


def check_doc_only_featfix(title: str, paths: list[str]) -> list[str]:
    if FEATFIX_RE.match(title or "") and paths and all(is_doc_only_path(p) for p in paths):
        return [f"title '{title.strip()[:80]}' is feat/fix but only docs/outputs/knowledge md/intake changed"]
    return []


def check_content(path: str, text: str | None) -> list[str]:
    out = []
    if not text:
        return out
    for n, line in enumerate(text.splitlines(), 1):
        if MARKER_RE.search(line):
            out.append(f"{path}:{n}: line is a stub marker ({line.strip()[:60]})")
            break
        if line.startswith(TMP_PREFIX):
            out.append(f"{path}:{n}: line starts with {TMP_PREFIX}")
            break
    return out


def check_shrink(path: str, old: str | None, new: str | None, status: str = "modified") -> list[str]:
    if not is_code(path) or status in ("added", "removed") or old is None:
        return []
    before, after = line_count(old), line_count(new)
    if before == 0:
        return []
    if after < before * (1 - SHRINK_RATIO):
        return [f"{path}: shrank {before}->{after} lines (>{int(SHRINK_RATIO * 100)}%)"]
    if after < MIN_LINES <= before:
        return [f"{path}: shrank to {after} lines (<{MIN_LINES})"]
    return []


def check_body(body: str | None) -> list[str]:
    body = body or ""
    out = []
    if not HO_RE.search(body):
        out.append("PR body has no handoff id (HO-...)")
    if not EVIDENCE_RE.search(body):
        out.append("PR body has no 'Test:' or 'CI:' line")
    return out


def extract_run_refs(body: str | None) -> list[dict]:
    """[{id, repo}] in order, deduped; repo is None for bare references."""
    refs: dict[int, dict] = {}
    body = body or ""
    for m in RUN_URL_RE.finditer(body):
        refs.setdefault(int(m.group(2)), {"id": int(m.group(2)), "repo": m.group(1)})
    for m in RUN_BARE_RE.finditer(body):
        refs.setdefault(int(m.group(1)), {"id": int(m.group(1)), "repo": None})
    return list(refs.values())


def check_run_refs(runs: list[dict], repo: str, head_sha: str) -> tuple[list[str], list[str]]:
    """runs: [{id, ref_repo, run (API dict) or None, error}] -> (reasons, warnings)."""
    reasons: list[str] = []
    warnings: list[str] = []
    for r in runs:
        rid = r["id"]
        if r.get("ref_repo") and r["ref_repo"].lower() != repo.lower():
            reasons.append(f"run {rid} belongs to another repo ({r['ref_repo']})")
            continue
        run = r.get("run")
        if not run:
            reasons.append(f"run {rid} could not be fetched ({r.get('error', 'not found')})")
            continue
        run_repo = ((run.get("repository") or {}).get("full_name") or repo)
        if run_repo.lower() != repo.lower():
            reasons.append(f"run {rid} belongs to another repo ({run_repo})")
            continue
        concl = run.get("conclusion")
        if run.get("status") != "completed" or concl != "success":
            reasons.append(f"run {rid} conclusion is {concl or run.get('status')} (not success)")
        if head_sha and run.get("head_sha") and run["head_sha"] != head_sha:
            warnings.append(f"run {rid} head_sha {run['head_sha'][:7]} != PR head {head_sha[:7]}")
    return reasons, warnings


def check_evidence_words(body: str | None) -> list[str]:
    lines = (body or "").splitlines()
    out = []
    for i, line in enumerate(lines):
        if not EVIDENCE_LINE_RE.match(line):
            continue
        for chunk in lines[i:i + 2]:
            m = FAIL_WORD_RE.search(chunk)
            if m:
                out.append(f"evidence line {i + 1} mentions '{m.group(1)}': {line.strip()[:80]}")
                break
    return out


def check_head_checks(check_runs: list[dict]) -> list[str]:
    out = []
    for c in check_runs:
        if c.get("name") == CHECK_NAME or c.get("status") != "completed":
            continue
        if c.get("conclusion") in BAD_CONCLUSIONS:
            out.append(f"check `{c.get('name')}` on head is {c['conclusion']}")
    return out


def check_ci_pending(check_runs: list[dict] | None, ci_pending: bool, strict: bool) -> list[str]:
    """Dispatch mode: payload flag or any unfinished non-auditor check -> fail."""
    if ci_pending:
        return [CI_PENDING_REASON + " (client_payload.ci_pending=true)"]
    if not strict:
        return []
    waiting = [c.get("name", "?") for c in check_runs or []
               if c.get("name") not in PENDING_IGNORE and c.get("status") != "completed"]
    return [f"{CI_PENDING_REASON} ({', '.join(waiting)})"] if waiting else []


def evaluate(title: str, files: list[dict], body: str | None = None,
             head_ref: str = "", check_pr_body: bool = True,
             run_refs: list[dict] | None = None, head_checks: list[dict] | None = None,
             repo: str = "", head_sha: str = "", ci_pending: bool = False,
             strict_pending: bool = False) -> dict:
    """Pure verdict. files: [{filename, status, old_text, new_text}]."""
    reasons: list[str] = []
    warnings: list[str] = []
    paths = [f["filename"] for f in files]
    if not files:
        reasons.append("no changed files found")
    reasons += check_doc_only_featfix(title, paths)
    for f in files:
        if f.get("status") != "removed":
            reasons += check_content(f["filename"], f.get("new_text"))
        reasons += check_shrink(f["filename"], f.get("old_text"), f.get("new_text"), f.get("status", "modified"))
    if check_pr_body:
        body_issues = check_body(body)
        if head_ref.startswith("bot/"):
            reasons += body_issues
        else:
            warnings += body_issues
        reasons += check_evidence_words(body)
    reasons += check_head_checks(head_checks or [])
    reasons += check_ci_pending(head_checks, ci_pending, strict_pending)
    if check_pr_body:
        if run_refs:
            run_reasons, run_warnings = check_run_refs(run_refs, repo, head_sha)
            reasons += run_reasons
            warnings += run_warnings
    verdict = "fail" if reasons else "pass"
    return {"verdict": verdict, "reasons": reasons, "warnings": warnings}


def api_json(url: str, token: str) -> Any:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "takipci-denetci",
    })
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_file_text(token: str, repo: str, ref: str, path: str) -> str | None:
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
    try:
        data = api_json(url, token)
        if isinstance(data, dict) and data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8", "replace")
        return None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def collect_changed_files(token: str, repo: str, base: str, head: str) -> list[dict]:
    """Files changed between base and head (names, statuses, old/new text)."""
    url = f"https://api.github.com/repos/{repo}/compare/{base}...{head}"
    data = api_json(url, token)
    out = []
    for f in data.get("files", []):
        out.append({
            "filename": f["filename"],
            "status": f["status"],
            "old_text": fetch_file_text(token, repo, base, f["filename"]),
            "new_text": fetch_file_text(token, repo, head, f["filename"]),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="takipci-denetci PR/commit auditor")
    ap.add_argument("--pr", type=int)
    ap.add_argument("--head-sha")
    ap.add_argument("--base")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--dispatch", action="store_true")
    ap.add_argument("--ci-pending", default="false")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        print("GITHUB_REPOSITORY not set", file=sys.stderr)
        return 1

    if args.pr:
        pr = api_json(f"https://api.github.com/repos/{repo}/pulls/{args.pr}", token)
        head = pr["head"]["sha"]
        base = pr["base"]["sha"]
        title = pr["title"]
        body = pr["body"] or ""
        head_ref = pr["head"]["ref"]
        files = collect_changed_files(token, repo, base, head)
        run_refs = extract_run_refs(body)
        check_runs = api_json(f"https://api.github.com/repos/{repo}/commits/{head}/check-runs", token)
        verdict = evaluate(title, files, body, head_ref, True,
                           run_refs, check_runs.get("check_runs", []), repo, head)
    else:
        head = args.head_sha or os.environ.get("GITHUB_SHA", "")
        base = args.base or "main"
        pr = None
        title = "merge"
        body = ""
        head_ref = ""
        files = collect_changed_files(token, repo, base, head)
        check_runs = api_json(f"https://api.github.com/repos/{repo}/commits/{head}/check-runs", token)
        strict = args.dispatch and args.ci_pending.lower() == "true"
        verdict = evaluate(title, files, body, head_ref, False, None,
                           check_runs.get("check_runs", []), repo, head,
                           args.dispatch, strict)

    print(json.dumps(verdict, ensure_ascii=False, indent=2))

    if args.publish:
        conclusion = "success" if verdict["verdict"] == "pass" else "failure"
        payload = {
            "name": CHECK_NAME,
            "head_sha": head,
            "status": "completed",
            "conclusion": conclusion,
            "output": {
                "title": f"takipci-denetci: {verdict['verdict']}",
                "summary": "\n".join(verdict["reasons"] or ["All rules passed."]),
                "text": json.dumps(verdict, ensure_ascii=False, indent=2),
            },
        }
        if pr:
            payload["details_url"] = pr["html_url"]
        api_json(f"https://api.github.com/repos/{repo}/check-runs", token, payload=payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
