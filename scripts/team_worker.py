"""team-worker: event-triggered handoff worker that only ever opens PRs.

Extends the ai-worker-gpt56 stack (scripts.provider_config.make_failover_adapter
+ scripts.worker_adapters) with a PR-only delivery path:

* works only on branch ``bot/<handoff_id>-<run_id>``; any push to main/master
  or to a non-bot ref is refused before git is called;
* never dispatches publish/payment workflows and refuses any diff that touches
  them (DENYLIST);
* no model key / no model answer -> writes a ``YAPAMADIM: <reason>`` note into
  state/handoffs.json and opens a PR for it (falls back to an issue); never a
  silent skip;
* runs the test suite; red tests -> PR opened as draft with the reason;
* idempotent: an open PR whose head starts with ``bot/<handoff_id>-`` blocks a
  new one;
* secret values are never printed (redact() scrubs every *_KEY/*_TOKEN value).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

UTC = timezone.utc
HANDOFFS = Path("state/handoffs.json")
RESULT_DIR = Path("state/team_work")
WORKER_TARGETS = {"grok", "worker", "team-worker"}
HANDOFF_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
PROTECTED_BRANCHES = {"main", "master", "HEAD"}

# Publish / payment surfaces: never dispatched, never modified by this bot.
DENYLIST_PATTERNS = (
    re.compile(r"youtube[-_]upload", re.I),
    re.compile(r"shorts[-_]free[-_](render|publish)", re.I),
    re.compile(r"(^|/)meta[-_]", re.I),
    re.compile(r"shopify|gumroad|whop|payment|payout", re.I),
)


class TeamWorkerError(RuntimeError):
    pass


class PushRefused(TeamWorkerError):
    pass


class DenylistViolation(TeamWorkerError):
    pass


# ---------------------------------------------------------------- secrets ---
def _secret_values(env: Mapping[str, str]) -> list[str]:
    out = []
    for name, value in env.items():
        if re.search(r"(KEY|TOKEN|SECRET|PASSWORD)", name) and value and len(value.strip()) >= 6:
            out.append(value.strip())
    return sorted(out, key=len, reverse=True)


def redact(text: str, env: Mapping[str, str] | None = None) -> str:
    text = str(text)
    for value in _secret_values(os.environ if env is None else env):
        text = text.replace(value, "***")
    return re.sub(r"(xai-|sk-|AIza|ghp_|ghs_|github_pat_)[A-Za-z0-9_-]{8,}", r"\1***", text)


def log(event: str, **fields: Any) -> None:
    print(redact(json.dumps({"team_worker": event, **fields}, ensure_ascii=False)), flush=True)


# ------------------------------------------------------------------ guards ---
def is_denylisted(name: str) -> bool:
    return any(p.search(name) for p in DENYLIST_PATTERNS)


def assert_workflow_allowed(workflow: str) -> None:
    if is_denylisted(workflow):
        raise DenylistViolation(f"workflow '{workflow}' is on the publish/payment denylist")


def assert_diff_allowed(paths: list[str]) -> None:
    bad = [p for p in paths if is_denylisted(p)]
    if bad:
        raise DenylistViolation("diff touches denylisted publish/payment files: " + ", ".join(sorted(bad)))


def bot_branch(handoff_id: str, run_id: str) -> str:
    if not HANDOFF_ID_RE.match(handoff_id or ""):
        raise TeamWorkerError(f"invalid handoff_id: {handoff_id!r}")
    if not re.match(r"^[A-Za-z0-9_-]{1,40}$", str(run_id)):
        raise TeamWorkerError(f"invalid run_id: {run_id!r}")
    return f"bot/{handoff_id}-{run_id}"


def assert_push_target(ref: str) -> None:
    name = ref.split(":")[-1]
    name = name.removeprefix("refs/heads/")
    if name in PROTECTED_BRANCHES or not name.startswith("bot/"):
        raise PushRefused(f"refusing push to '{name}': team-worker only pushes bot/<handoff_id>-<run_id> branches")


# --------------------------------------------------------------------- git ---
def _git(*args: str, cwd: Path | None = None, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise TeamWorkerError(redact(f"git {' '.join(args)} failed: {proc.stderr.strip()}"))
    return proc.stdout


def git_push_branch(branch: str, cwd: Path | None = None) -> None:
    assert_push_target(branch)
    _git("push", "origin", f"HEAD:refs/heads/{branch}", cwd=cwd)


def changed_paths(base: str = "origin/main", cwd: Path | None = None) -> list[str]:
    committed = _git("diff", "--name-only", f"{base}...HEAD", cwd=cwd, check=False).split()
    working = _git("status", "--porcelain", cwd=cwd).splitlines()
    return sorted(set(committed) | {line[3:].strip() for line in working if line.strip()})


# ------------------------------------------------------------- GitHub API ---
class GitHubClient:
    def __init__(self, repo: str, token: str, api: str = "https://api.github.com"):
        self.repo, self.token, self.api = repo, token, api.rstrip("/")

    def _call(self, method: str, path: str, payload: dict | None = None) -> Any:
        req = Request(
            f"{self.api}/repos/{self.repo}{path}",
            data=None if payload is None else json.dumps(payload).encode(),
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode() or "null")
        except HTTPError as exc:
            body = exc.read().decode(errors="replace")[:300]
            raise TeamWorkerError(redact(f"GitHub API {method} {path} -> {exc.code}: {body}")) from exc

    def list_open_pulls(self) -> list[dict]:
        return self._call("GET", "/pulls?state=open&per_page=100") or []

    def create_pull(self, *, head: str, base: str, title: str, body: str, draft: bool) -> dict:
        return self._call("POST", "/pulls", {"head": head, "base": base, "title": title, "body": body, "draft": draft})

    def repository_dispatch(self, event_type: str, client_payload: dict) -> None:
        assert_workflow_allowed(event_type)
        self._call("POST", "/dispatches", {"event_type": event_type, "client_payload": client_payload})

    def create_issue(self, *, title: str, body: str) -> dict:
        return self._call("POST", "/issues", {"title": title, "body": body, "labels": ["team-worker"]})


RESEARCH_EVENT = "team-research"
RESEARCH_MARKER = "team-research dispatched"


def trigger_research(client: Any, item: dict, handoff_id: str, reason: str, task: str) -> bool:
    """Fire research-learner once per handoff (marker in main's handoff notes)."""
    if any(RESEARCH_MARKER in str(n) or "research-learner (team-research)" in str(n) for n in item.get("notes") or []):
        log("research_already_dispatched", handoff_id=handoff_id)
        return False
    client.repository_dispatch(RESEARCH_EVENT, {"handoff_id": handoff_id, "reason": reason[:500], "task": task[:1000]})
    log("research_dispatched", handoff_id=handoff_id, event_type=RESEARCH_EVENT)
    return True


def find_open_pr(client: Any, handoff_id: str) -> dict | None:
    prefix = f"bot/{handoff_id}-"
    for pr in client.list_open_pulls():
        if str((pr.get("head") or {}).get("ref", "")).startswith(prefix):
            return pr
    return None


# ---------------------------------------------------------------- handoffs ---
def load_handoffs(path: Path = HANDOFFS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_handoff(data: dict, handoff_id: str) -> dict | None:
    return next((i for i in data.get("items", []) if i.get("id") == handoff_id), None)


def _is_migrated(item: dict) -> bool:
    return str(item.get("source", "")).lower() == "backlog-migration" or any(
        "migrated" in str(n).lower() for n in item.get("notes") or [])


def pending_worker_handoffs(data: dict) -> list[str]:
    """Push-trigger candidates, oldest first. Migrated/backlog items are never auto-picked
    (only workflow_dispatch / repository_dispatch may start them)."""
    items = [
        i for i in data.get("items", [])
        if i.get("status") == "open" and str(i.get("to", "")).lower() in WORKER_TARGETS and i.get("id")
        and not any("team-worker:" in str(n) for n in i.get("notes") or [])
        and not _is_migrated(i)
    ]
    items.sort(key=lambda i: (str(i.get("created_at", "")), str(i["id"])))
    return [str(i["id"]) for i in items]


def append_note(path: Path, handoff_id: str, note: str, now: str) -> None:
    data = load_handoffs(path)
    item = find_handoff(data, handoff_id)
    if item is None:
        raise TeamWorkerError(f"handoff {handoff_id} not found in {path}")
    item.setdefault("notes", []).append(f"{now} team-worker: {note}")
    item["updated_at"] = now
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ------------------------------------------------------------------- model ---
def default_adapter_factory(env: Mapping[str, str]):
    from scripts.provider_config import make_failover_adapter
    return make_failover_adapter(env=env)


def run_model(task: str, handoff_id: str, env: Mapping[str, str],
              adapter_factory: Callable[[Mapping[str, str]], Any]) -> tuple[dict | None, str | None]:
    """Returns (result, None) or (None, YAPAMADIM reason). Never raises for provider issues."""
    try:
        adapter = adapter_factory(env)
    except Exception as exc:  # MissingCredential / ConfigError
        return None, redact(f"model anahtari yok veya yapilandirilamadi ({type(exc).__name__}: {exc})", env)
    job = {"id": handoff_id, "project": "ai-shared-workspace", "objective": task,
           "evidence_requirements": ["repo-relative paths or commit SHAs for every claim"]}
    try:
        result = adapter.run(job)
    except Exception as exc:
        return None, redact(f"model cevap vermedi ({type(exc).__name__}: {exc})", env)
    if not isinstance(result, dict) or not (result.get("recommendation") or result.get("factual_findings")):
        return None, "model bos/gecersiz cevap dondu"
    return result, None


def run_tests(cmd: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    tail = (proc.stdout + proc.stderr)[-1500:]
    return proc.returncode == 0, redact(tail)


# --------------------------------------------------------------- pipeline ---
DEFAULT_TEST_CMD = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]


def process_handoff(
    handoff_id: str,
    *,
    run_id: str,
    client: Any,
    env: Mapping[str, str],
    task: str | None = None,
    source: str = "manual",
    dry_run: bool = False,
    root: Path = Path("."),
    adapter_factory: Callable[[Mapping[str, str]], Any] = default_adapter_factory,
    test_runner: Callable[[], tuple[bool, str]] | None = None,
    git_ops: Any = None,
    now: str | None = None,
) -> dict:
    now = now or datetime.now(UTC).isoformat(timespec="seconds")
    branch = bot_branch(handoff_id, run_id)
    handoffs_path = root / HANDOFFS
    item = find_handoff(load_handoffs(handoffs_path), handoff_id)
    if item is None:
        raise TeamWorkerError(f"handoff {handoff_id} not found")
    task = task or str(item.get("task", ""))

    existing = find_open_pr(client, handoff_id)
    if existing:
        log("skip_existing_pr", handoff_id=handoff_id, pr=existing.get("html_url") or existing.get("number"))
        return {"status": "exists", "pr": existing.get("html_url") or existing.get("number"), "branch": None}

    git = git_ops or _RealGit(root)
    git.checkout_new(branch)

    result, failure = run_model(task, handoff_id, env, adapter_factory)
    if failure:
        research = False
        if not dry_run:
            try:
                research = trigger_research(client, item, handoff_id, failure, task)
            except TeamWorkerError as exc:
                log("research_dispatch_failed", handoff_id=handoff_id, reason=str(exc))
        append_note(handoffs_path, handoff_id,
                    f"YAPAMADIM: {failure}" + (f" | {RESEARCH_MARKER} ({RESEARCH_EVENT})" if research else ""), now)
        title = f"team-worker: YAPAMADIM {handoff_id}"
    else:
        out = root / RESULT_DIR / f"{handoff_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"handoff_id": handoff_id, "source": source, "run_id": run_id,
                                   "task": task, "generated_at": now, "result": result},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        append_note(handoffs_path, handoff_id,
                    f"model sonucu {RESULT_DIR.as_posix()}/{handoff_id}.json ({result.get('provider')}/{result.get('model')}), PR bekliyor",
                    now)
        title = f"team-worker: {handoff_id}"

    assert_diff_allowed(git.changed_paths())

    tests_ok, test_tail = (test_runner or (lambda: run_tests(DEFAULT_TEST_CMD, root)))()
    draft = not tests_ok
    body_lines = [f"Handoff: `{handoff_id}` (source: {source}, run: {run_id})", f"Gorev: {task}", ""]
    body_lines.append(f"**YAPAMADIM:** {failure}" if failure else
                      f"Model sonucu: `{RESULT_DIR.as_posix()}/{handoff_id}.json`\n\nOneri: {result.get('recommendation', '')}")
    body_lines += ["", "Testler: " + ("YESIL" if tests_ok else "KIRMIZI -> PR draft acildi. Neden:\n```\n" + test_tail + "\n```")]
    body = redact("\n".join(body_lines), env)

    if dry_run:
        log("dry_run", handoff_id=handoff_id, branch=branch, draft=draft, yapamadim=bool(failure))
        return {"status": "dry_run", "branch": branch, "draft": draft, "yapamadim": failure, "tests_ok": tests_ok}

    git.commit(title)
    try:
        git.push(branch)
        pr = client.create_pull(head=branch, base="main", title=title, body=body, draft=draft)
        log("pr_opened", handoff_id=handoff_id, pr=pr.get("html_url"), draft=draft)
        return {"status": "pr", "pr": pr.get("html_url"), "branch": branch, "draft": draft, "yapamadim": failure}
    except PushRefused:
        raise
    except TeamWorkerError as exc:
        issue = client.create_issue(title=title, body=body + f"\n\nPR acilamadi: {redact(str(exc), env)}")
        log("issue_opened", handoff_id=handoff_id, issue=issue.get("html_url"))
        return {"status": "issue", "issue": issue.get("html_url"), "branch": branch, "yapamadim": failure}


class _RealGit:
    def __init__(self, root: Path):
        self.root = root

    def checkout_new(self, branch: str) -> None:
        assert_push_target(branch)
        _git("checkout", "-B", branch, cwd=self.root)

    def changed_paths(self) -> list[str]:
        return changed_paths(cwd=self.root)

    def commit(self, message: str) -> None:
        _git("config", "user.name", "team-worker-bot", cwd=self.root)
        _git("config", "user.email", "team-worker-bot@users.noreply.github.com", cwd=self.root)
        _git("add", "-A", "state/handoffs.json", "state/team_work", cwd=self.root)
        _git("commit", "-m", message, cwd=self.root)

    def push(self, branch: str) -> None:
        git_push_branch(branch, cwd=self.root)


def resolve_targets(event_name: str, event: dict, cli_id: str | None, data: dict) -> list[tuple[str, str | None, str]]:
    if cli_id:
        return [(cli_id, None, "workflow_dispatch")]
    if event_name == "repository_dispatch":
        p = event.get("client_payload") or {}
        if not p.get("handoff_id"):
            raise TeamWorkerError("repository_dispatch client_payload.handoff_id missing")
        return [(str(p["handoff_id"]), p.get("task"), str(p.get("source") or "repository_dispatch"))]
    if event_name == "workflow_dispatch":
        hid = (event.get("inputs") or {}).get("handoff_id")
        if not hid:
            raise TeamWorkerError("workflow_dispatch input handoff_id missing")
        return [(str(hid), None, "workflow_dispatch")]
    # Push trigger: at most ONE job per commit (oldest); the rest stay queued for later pushes/dispatches.
    return [(hid, None, "push") for hid in pending_worker_handoffs(data)[:1]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handoff-id")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    env = os.environ
    event_path = env.get("GITHUB_EVENT_PATH")
    event = json.loads(Path(event_path).read_text()) if event_path and Path(event_path).exists() else {}
    targets = resolve_targets(env.get("GITHUB_EVENT_NAME", ""), event, args.handoff_id, load_handoffs())
    if not targets:
        log("no_pending_handoff")
        return 0
    client = GitHubClient(env["GITHUB_REPOSITORY"], env["GITHUB_TOKEN"])
    run_id = env.get("GITHUB_RUN_ID", "local")
    rc = 0
    for hid, task, source in targets:
        try:
            outcome = process_handoff(hid, run_id=run_id, client=client, env=env, task=task,
                                      source=source, dry_run=args.dry_run)
            log("done", handoff_id=hid, **{k: v for k, v in outcome.items() if k != "yapamadim"},
                yapamadim=outcome.get("yapamadim"))
        except (DenylistViolation, PushRefused) as exc:
            log("refused", handoff_id=hid, reason=str(exc))
            rc = 1
        _git("checkout", "--force", "main", check=False)
        _git("reset", "--hard", "origin/main", check=False)
        _git("clean", "-fd", "state/team_work", check=False)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
