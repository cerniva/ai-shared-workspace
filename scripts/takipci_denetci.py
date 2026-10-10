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
    for m in MARKERS:
        if m in text:
            out.append(f"{path}: contains {m}")
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


def evaluate(title: str, files: list[dict], body: str | None = None,
             head_ref: str = "", check_pr_body: bool = True) -> dict:
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


def audit_pr(gh: GitHub, number: int) -> tuple[dict, str]:
    pr = gh.request("GET", f"/pulls/{number}")
    head = pr["head"]["sha"]
    files = collect(gh, gh.paged(f"/pulls/{number}/files"), pr["base"]["sha"], head)
    res = evaluate(pr.get("title", ""), files, pr.get("body"), pr["head"].get("ref", ""))
    res.update(pr_number=number, head_sha=head)
    return res, head


def audit_commit(gh: GitHub, sha: str, base: str | None = None) -> dict:
    commit = gh.request("GET", f"/commits/{sha}")
    parents = commit.get("parents") or []
    base = base or (parents[0]["sha"] if parents else None)
    title = (commit.get("commit", {}).get("message") or "").splitlines()[0:1]
    files = collect(gh, commit.get("files") or [], base, sha)
    res = evaluate(title[0] if title else "", files, check_pr_body=False)
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
    args = p.parse_args(argv)
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        print("GITHUB_REPOSITORY/GITHUB_TOKEN missing", file=sys.stderr)
        return 2
    gh = GitHub(repo, token)
    if args.pr:
        res, sha = audit_pr(gh, args.pr)
    elif args.head_sha:
        res, sha = audit_commit(gh, args.head_sha, args.base), args.head_sha
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
