#!/usr/bin/env python3
"""takipci-denetci: rule-based PR/commit auditor (no model, no API keys).

Inspects the files changed by a PR (or a merge commit) via the GitHub API with
GITHUB_TOKEN and emits a JSON verdict {verdict, reasons, warnings}. Rules:
  1. feat/fix title but only docs/outputs/knowledge/*.md/intake changed -> fail
  2. a changed file contains the stub markers (see MARKERS) or a line that
     starts with the tmp-file paste prefix (see TMP_PREFIX) -> fail
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


def check_content(path: str, text: str | None, old_text: str | None = None) -> list[str]:
    out = []
    if not text:
        return out
    for m in MARKERS:
        if m in text and (old_text is None or m not in old_text):
            out.append(f"{path}: introduced {m}")
    for n, line in enumerate(text.splitlines(), 1):
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
            reasons += check_content(f["filename"], f.get("new_text"), f.get("old_text"))
        reasons += check_shrink(f["filename"], f.get("old_text"), f.get("new_text"), f.get("status", "modified"))
    if check_pr_body:
        body_issues = check_body(body)
        if head_ref.startswith("bot/"):
            reasons += body_issues
        else:
            warnings += body_issues
        reasons += check_evidence_words(body)
    if run_refs is not None:
        r, w = check_run_refs(run_refs, repo, head_sha)
        reasons += r
        warnings += w
    if head_checks is not None:
        reasons += check_head_checks(head_checks)
    reasons += check_ci_pending(head_checks, ci_pending, strict_pending)
    return {"check": CHECK_NAME, "verdict": "fail" if reasons else "pass",
            "reasons": reasons, "warnings": warnings, "files": paths}


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

    def paged(self, path: str) -> list:
        out, page = [], 1
        sep = "&" if "?" in path else "?"
        while True:
            items = self.request("GET", f"{path}{sep}per_page=100&page={page}")
            out.extend(items)
            if len(items) < 100:
                return out
            page += 1

    def text_at(self, path: str, ref: str) -> str | None:
        try:
            res = self.request("GET", f"/contents/{urllib.parse.quote(path)}?ref={ref}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
        if not isinstance(res, dict) or res.get("encoding") != "base64":
            return None
        try:
            return base64.b64decode(res.get("content", "")).decode("utf-8")
        except UnicodeDecodeError:
            return None


def collect(gh: GitHub, raw_files: list[dict], base: str | None, head: str) -> list[dict]:
    out = []
    for f in raw_files:
        name, status = f["filename"], f.get("status", "modified")
        prev = f.get("previous_filename") or name
        new = None if status == "removed" else gh.text_at(name, head)
        old = gh.text_at(prev, base) if base and status != "added" else None
        out.append({"filename": name, "status": status, "old_text": old, "new_text": new})
    return out


def fetch_run_refs(gh: GitHub, refs: list[dict]) -> list[dict]:
    out = []
    for ref in refs:
        item = {"id": ref["id"], "ref_repo": ref.get("repo"), "run": None}
        if not ref.get("repo") or ref["repo"].lower() == gh.repo.lower():
            try:
                item["run"] = gh.request("GET", f"/actions/runs/{ref['id']}")
            except urllib.error.HTTPError as e:
                item["error"] = f"HTTP {e.code}"
        out.append(item)
    return out


def head_check_runs(gh: GitHub, sha: str) -> list[dict]:
    return gh.request("GET", f"/commits/{sha}/check-runs?per_page=100").get("check_runs", [])


def audit_pr(gh: GitHub, number: int, dispatch: bool = False, ci_pending: bool = False) -> tuple[dict, str]:
    pr = gh.request("GET", f"/pulls/{number}")
    head = pr["head"]["sha"]
    files = collect(gh, gh.paged(f"/pulls/{number}/files"), pr["base"]["sha"], head)
    run_refs = fetch_run_refs(gh, extract_run_refs(pr.get("body")))
    checks = head_check_runs(gh, head)
    res = evaluate(pr.get("title", ""), files, pr.get("body"), pr["head"].get("ref", ""),
                   run_refs=run_refs, head_checks=checks, repo=gh.repo, head_sha=head,
                   ci_pending=ci_pending, strict_pending=dispatch)
    res.update(pr_number=number, head_sha=head)
    return res, head


def audit_commit(gh: GitHub, sha: str, base: str | None = None,
                 dispatch: bool = False, ci_pending: bool = False) -> dict:
    commit = gh.request("GET", f"/commits/{sha}")
    parents = commit.get("parents") or []
    base = base or (parents[0]["sha"] if parents else None)
    title = (commit.get("commit", {}).get("message") or "").splitlines()[0:1]
    files = collect(gh, commit.get("files") or [], base, sha)
    checks = head_check_runs(gh, sha) if dispatch else None
    res = evaluate(title[0] if title else "", files, check_pr_body=False, head_checks=checks,
                   ci_pending=ci_pending, strict_pending=dispatch)
    res.update(head_sha=sha, base_sha=base)
    return res


def publish_check(gh: GitHub, sha: str, res: dict) -> dict:
    lines = [f"- FAIL: {r}" for r in res["reasons"]] + [f"- WARN: {w}" for w in res["warnings"]]
    summary = f"verdict: {res['verdict']} ({len(res['files'])} files)"
    return gh.request("POST", "/check-runs", {
        "name": CHECK_NAME, "head_sha": sha, "status": "completed",
        "conclusion": "success" if res["verdict"] == "pass" else "failure",
        "output": {"title": f"{CHECK_NAME}: {res['verdict']}", "summary": summary,
                   "text": "\n".join(lines) or "no findings"}})


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--pr", type=int)
    p.add_argument("--head-sha")
    p.add_argument("--base")
    p.add_argument("--publish", action="store_true", help="post check run on the audited head SHA")
    p.add_argument("--dispatch", action="store_true", help="team-pr-opened mode: unfinished CI -> fail")
    p.add_argument("--ci-pending", default="", help="client_payload.ci_pending (true/false)")
    args = p.parse_args(argv)
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        print("GITHUB_REPOSITORY/GITHUB_TOKEN missing", file=sys.stderr)
        return 2
    gh = GitHub(repo, token)
    pending = str(args.ci_pending).strip().lower() in ("1", "true", "yes")
    if args.pr:
        res, sha = audit_pr(gh, args.pr, dispatch=args.dispatch, ci_pending=pending)
    elif args.head_sha:
        res = audit_commit(gh, args.head_sha, args.base, dispatch=args.dispatch, ci_pending=pending)
        sha = args.head_sha
    else:
        p.error("--pr or --head-sha required")
    if args.publish:
        run = publish_check(gh, sha, res)
        res["check_run_url"] = run.get("html_url")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    out = os.environ.get("TAKIPCI_OUT")
    if out:
        Path(out).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return 0 if res["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
