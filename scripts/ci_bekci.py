#!/usr/bin/env python3
"""ci-bekci: rule-based CI failure watcher (no model, no new secrets).

Runs on GitHub Actions (workflow_run completed / workflow_dispatch run_id) with
GITHUB_TOKEN only. For a failed/timed_out run it fetches the run, its failed jobs,
failed step names and the last ~60 log lines of each failed job, extracts the
first error-looking lines and failing test ids with regexes, and then:

  * dedupes against OPEN issues labelled `ci-bekci` carrying the hidden marker
    <!-- ci-bekci:<workflow>:<signature> --> (never writes to main / state files);
      - same workflow+signature already open: comment only when head_sha is new;
      - otherwise opens a new issue and sends ONE repository_dispatch `team-work`
        {handoff_id: CI-<run_id>, task, source: ci-bekci, run_id, head_sha},
        capped at MAX_DISPATCH_PER_DAY (counted from ci-bekci issues created today, UTC).
  * for a successful run on main: closes open ci-bekci issues of that workflow
    with a comment linking the green run.

Loop guard: runs of ci-bekci, takipci-denetci, auto-merge-gate, team-worker and any
upload/publish/payment/gumroad/shopify workflow are ignored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

LABEL = "ci-bekci"
DISPATCH_EVENT = "team-work"
SOURCE = "ci-bekci"
MAX_DISPATCH_PER_DAY = 3
LOG_TAIL_LINES = 60
MAX_ERROR_LINES = 8
FAIL_CONCLUSIONS = ("failure", "timed_out")

EXCLUDED_WORKFLOWS = frozenset({"ci-bekci", "takipci-denetci", "auto-merge-gate", "team-worker"})
EXCLUDED_KEYWORDS = ("upload", "publish", "payment", "gumroad", "shopify")

ERROR_RE = re.compile(
    r"(AssertionError|ModuleNotFoundError|SyntaxError|Traceback \(most recent call last\)"
    r"|\bFAILED\b|\bERROR\b|\bError\b|[A-Za-z]+Error:|exit code \d+|##\[error\])"
)
TEST_ID_RE = re.compile(r"^(?:FAIL|ERROR): (test\w*) \(([\w.]+)\)")
PYTEST_ID_RE = re.compile(r"^FAILED ([\w/.\-]+\.py::[\w:\[\]\-.]+)")
TS_PREFIX_RE = re.compile(r"^\ufeff?\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z ?")
MARKER_RE = re.compile(r"<!-- ci-bekci:(?P<workflow>.+?):(?P<signature>[0-9a-f]{6,40}|none) -->")
SHA_MARKER_RE = re.compile(r"<!-- ci-bekci-sha:(?P<sha>[0-9a-f]{7,40}) -->")


# ------------------------------------------------------------ pure helpers ---
def is_excluded(workflow_name: str) -> bool:
    name = (workflow_name or "").strip().lower()
    return name in EXCLUDED_WORKFLOWS or any(k in name for k in EXCLUDED_KEYWORDS)


def clean_line(line: str) -> str:
    line = TS_PREFIX_RE.sub("", line.rstrip("\r\n"))
    return line.replace("##[error]", "").strip()


def tail(text: str, n: int = LOG_TAIL_LINES) -> list[str]:
    lines = [clean_line(x) for x in (text or "").splitlines()]
    lines = [x for x in lines if x]
    return lines[-n:]


def extract_errors(lines: list[str], limit: int = MAX_ERROR_LINES) -> list[str]:
    out: list[str] = []
    for raw in lines:
        line = clean_line(raw)
        if line and ERROR_RE.search(line) and line not in out:
            out.append(line[:300])
            if len(out) >= limit:
                break
    return out


def extract_test_ids(lines: list[str]) -> list[str]:
    out: list[str] = []
    for raw in lines:
        line = clean_line(raw)
        m = TEST_ID_RE.match(line)
        tid = f"{m.group(1)} ({m.group(2)})" if m else None
        if not tid:
            p = PYTEST_ID_RE.match(line)
            tid = p.group(1) if p else None
        if tid and tid not in out:
            out.append(tid)
    return out


def normalize_error(line: str) -> str:
    s = clean_line(line)
    s = re.sub(r"0x[0-9a-fA-F]+", "<hex>", s)
    s = re.sub(r"\b[0-9a-f]{7,40}\b", "<sha>", s)
    s = re.sub(r"(/[\w.\-]+)+/", "", s)  # drop directory prefixes (runner paths vary)
    s = re.sub(r"\d+(\.\d+)?", "<n>", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def signature(errors: list[str], test_ids: list[str] | None = None) -> str:
    """Stable 12-hex signature of the failure: first failing test id, else first error line."""
    basis = (test_ids or [None])[0] or (normalize_error(errors[0]) if errors else "")
    if not basis:
        return "none"
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]


def marker(workflow: str, sig: str) -> str:
    return f"<!-- ci-bekci:{workflow}:{sig} -->"


def sha_marker(sha: str) -> str:
    return f"<!-- ci-bekci-sha:{sha} -->"


def parse_marker(body: str | None) -> tuple[str, str] | None:
    m = MARKER_RE.search(body or "")
    return (m.group("workflow"), m.group("signature")) if m else None


def find_issue(issues: list[dict], workflow: str, sig: str) -> dict | None:
    for it in issues:
        if "pull_request" not in it and parse_marker(it.get("body")) == (workflow, sig):
            return it
    return None


def known_shas(issue: dict, comments: list[dict]) -> set[str]:
    text = (issue.get("body") or "") + "".join(c.get("body") or "" for c in comments)
    return {m.group("sha") for m in SHA_MARKER_RE.finditer(text)}


def count_created_today(issues: list[dict], today: str) -> int:
    return sum(1 for it in issues if "pull_request" not in it and str(it.get("created_at", "")).startswith(today))


def dispatch_allowed(created_today: int, cap: int = MAX_DISPATCH_PER_DAY) -> bool:
    """created_today counts ci-bekci issues created today INCLUDING the one just opened."""
    return created_today <= cap


def should_close_on_green(run: dict) -> bool:
    return (run.get("conclusion") == "success" and run.get("head_branch") == "main"
            and run.get("event") != "pull_request" and not is_excluded(run.get("name", "")))


def issues_to_close(issues: list[dict], workflow: str) -> list[dict]:
    out = []
    for it in issues:
        mk = parse_marker(it.get("body"))
        if "pull_request" not in it and mk and mk[0] == workflow:
            out.append(it)
    return out


def summarize(workflow: str, run_id: Any, failed: list[dict], errors: list[str], test_ids: list[str]) -> str:
    jobs = ", ".join(f"{j['name']}[{'/'.join(j.get('steps') or []) or '?'}]" for j in failed) or "?"
    head = test_ids[0] if test_ids else (errors[0] if errors else "no error line matched")
    return f"CI failure in '{workflow}' run {run_id}: jobs {jobs}; first error: {head}"[:900]


def issue_body(run: dict, failed: list[dict], errors: list[str], test_ids: list[str], sig: str) -> str:
    wf = run.get("name", "?")
    lines = [marker(wf, sig), sha_marker(run.get("head_sha", "")),
             f"**Workflow:** {wf}", f"**Run:** {run.get('html_url')}",
             f"**Conclusion:** {run.get('conclusion')}", f"**Branch:** {run.get('head_branch')}",
             f"**head_sha:** `{run.get('head_sha')}`", f"**Signature:** `{sig}`", "", "### Failed jobs / steps"]
    lines += [f"- {j['name']}: {', '.join(j.get('steps') or []) or '(no failed step reported)'} — {j.get('html_url', '')}"
              for j in failed] or ["- (none reported)"]
    if test_ids:
        lines += ["", "### Failing tests"] + [f"- `{t}`" for t in test_ids[:20]]
    lines += ["", "### Extracted error lines", "```"] + (errors or ["(no matching line)"]) + ["```",
              "", "_Rule-based (no model). Auto-closes when a later run of this workflow on main succeeds._"]
    return "\n".join(lines)


# ---------------------------------------------------------------- GitHub ---
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


class GitHub:
    def __init__(self, repo: str, token: str, api: str = "https://api.github.com"):
        self.repo, self.token, self.api = repo, token, api.rstrip("/")

    def _req(self, method: str, path: str, body: Any = None) -> urllib.request.Request:
        url = path if path.startswith("http") else f"{self.api}/repos/{self.repo}{path}"
        data = json.dumps(body).encode() if body is not None else None
        return urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})

    def request(self, method: str, path: str, body: Any = None) -> Any:
        with urllib.request.urlopen(self._req(method, path, body), timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}

    def paged(self, path: str, max_pages: int = 10) -> list:
        out, sep = [], "&" if "?" in path else "?"
        for page in range(1, max_pages + 1):
            items = self.request("GET", f"{path}{sep}per_page=100&page={page}")
            items = items.get("jobs", []) if isinstance(items, dict) else items
            out.extend(items)
            if len(items) < 100:
                break
        return out

    def job_log(self, job_id: int) -> str:
        """Job logs answer 302 -> signed URL; follow it WITHOUT the Authorization header."""
        opener = urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(self._req("GET", f"/actions/jobs/{job_id}/logs"), timeout=30) as resp:
                return resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location") if e.code in (301, 302, 303, 307, 308) else None
            if not loc:
                return f"(log unavailable: HTTP {e.code})"
        with urllib.request.urlopen(loc, timeout=60) as resp:
            return resp.read().decode("utf-8", "replace")


def log(event: str, **kw: Any) -> None:
    print(json.dumps({"ci_bekci": event, **kw}, ensure_ascii=False), flush=True)


def ensure_label(gh: GitHub) -> None:
    try:
        gh.request("POST", "/labels", {"name": LABEL, "color": "d93f0b",
                                       "description": "ci-bekci rule-based CI failure watcher"})
    except urllib.error.HTTPError as e:
        if e.code != 422:  # 422 = already exists
            raise


def open_issues(gh: GitHub) -> list[dict]:
    return gh.paged(f"/issues?state=open&labels={LABEL}")


def failed_jobs(gh: GitHub, run_id: Any) -> list[dict]:
    out = []
    for j in gh.paged(f"/actions/runs/{run_id}/jobs?filter=latest"):
        if j.get("conclusion") in FAIL_CONCLUSIONS:
            steps = [s["name"] for s in j.get("steps") or [] if s.get("conclusion") in FAIL_CONCLUSIONS]
            out.append({"id": j["id"], "name": j.get("name", "?"), "steps": steps, "html_url": j.get("html_url", "")})
    return out


def handle_failure(gh: GitHub, run: dict, dry_run: bool = False, today: str | None = None) -> dict:
    wf, run_id, sha = run.get("name", "?"), run["id"], run.get("head_sha", "")
    failed = failed_jobs(gh, run_id)
    lines: list[str] = []
    for j in failed:
        lines += tail(gh.job_log(j["id"]))
    errors, test_ids = extract_errors(lines), extract_test_ids(lines)
    sig = signature(errors, test_ids)
    summary = summarize(wf, run_id, failed, errors, test_ids)
    log("analyzed", workflow=wf, run_id=run_id, head_sha=sha, signature=sig, summary=summary)
    if dry_run:
        return {"action": "dry_run", "signature": sig, "summary": summary, "errors": errors, "tests": test_ids}
    ensure_label(gh)
    existing = find_issue(open_issues(gh), wf, sig)
    if existing:
        comments = gh.paged(f"/issues/{existing['number']}/comments")
        if sha in known_shas(existing, comments):
            log("duplicate_noop", issue=existing["number"])
            return {"action": "noop", "issue": existing["number"], "signature": sig}
        gh.request("POST", f"/issues/{existing['number']}/comments", {"body": "\n".join([
            sha_marker(sha), f"Same failure signature `{sig}` on new head_sha `{sha}`: {run.get('html_url')}"])})
        return {"action": "commented", "issue": existing["number"], "signature": sig}
    title = f"ci-bekci: {wf} failing ({sig})"
    issue = gh.request("POST", "/issues", {"title": title[:200], "labels": [LABEL],
                                           "body": issue_body(run, failed, errors, test_ids, sig)})
    today = today or datetime.now(UTC).strftime("%Y-%m-%d")
    created = count_created_today(gh.paged(f"/issues?state=all&labels={LABEL}&since={today}T00:00:00Z"), today)
    result = {"action": "opened", "issue": issue.get("number"), "signature": sig, "dispatched": False}
    if dispatch_allowed(created):
        gh.request("POST", "/dispatches", {"event_type": DISPATCH_EVENT, "client_payload": {
            "handoff_id": f"CI-{run_id}", "task": summary, "source": SOURCE,
            "run_id": str(run_id), "head_sha": sha}})
        result["dispatched"] = True
    else:
        gh.request("POST", f"/issues/{issue['number']}/comments",
                   {"body": f"Daily dispatch cap ({MAX_DISPATCH_PER_DAY}) reached; team-work not dispatched."})
    log("issue_opened", **result)
    return result


def handle_success(gh: GitHub, run: dict, dry_run: bool = False) -> dict:
    if not should_close_on_green(run):
        return {"action": "skip_success"}
    targets = issues_to_close(open_issues(gh), run.get("name", ""))
    if not dry_run:
        for it in targets:
            gh.request("POST", f"/issues/{it['number']}/comments", {"body":
                       f"Green: later run of `{run.get('name')}` on main succeeded: {run.get('html_url')} "
                       f"(head_sha `{run.get('head_sha')}`). Closing."})
            gh.request("PATCH", f"/issues/{it['number']}", {"state": "closed", "state_reason": "completed"})
    log("closed_on_green", issues=[it["number"] for it in targets], dry_run=dry_run)
    return {"action": "closed", "issues": [it["number"] for it in targets]}


def process_run(gh: GitHub, run: dict, dry_run: bool = False) -> dict:
    if is_excluded(run.get("name", "")):
        log("excluded", workflow=run.get("name"))
        return {"action": "excluded"}
    if run.get("conclusion") in FAIL_CONCLUSIONS:
        return handle_failure(gh, run, dry_run=dry_run)
    if run.get("conclusion") == "success":
        return handle_success(gh, run, dry_run=dry_run)
    return {"action": "ignored", "conclusion": run.get("conclusion")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    gh = GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    run = gh.request("GET", f"/actions/runs/{args.run_id}")
    res = process_run(gh, run, dry_run=args.dry_run)
    out = os.environ.get("GITHUB_STEP_SUMMARY")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"## ci-bekci run {args.run_id} ({run.get('name')})\n\n```json\n{json.dumps(res, indent=2, ensure_ascii=False)}\n```\n")
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
