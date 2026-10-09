#!/usr/bin/env python3
"""Backup supervisor: keeps the desk moving when Grok Bot is out of credits.

Each run (hourly via .github/workflows/backup-supervisor.yml):
  1. reads state/handoffs.json, latest CI runs on main, open desk messages;
  2. lists overdue handoff items (open > 2 h) in the status report;
  3. for open items explicitly flagged ``"supervisor_ok": true`` (small, safe,
     well-specified) asks the failover chain gemini -> deepseek -> claude ->
     openai for a unified diff and, only if it passes path rules (no .github/,
     no PayoutLens, no secrets, allowed prefixes, <= 64 KB) and
     ``git apply --check``, writes it to intake/chatgpt/ for normal review.
     It never edits code on main itself;
  4. writes a short Turkish status file messages/backup-supervisor-latest.md.
With no provider key it still writes the status file and exits 0 (skip).
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
from typing import Any
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import handoff  # noqa: E402
from scripts.chatgpt_intake import MAX_PATCH_BYTES, patch_paths, path_blockers  # noqa: E402
from scripts.provider_config import PROVIDER_ENV, FailoverAdapter, make_adapter  # noqa: E402
from scripts.worker_adapters import MissingCredential, WorkerError  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR_ORDER = ("gemini", "deepseek", "claude", "openai")
STATUS_PATH = ROOT / "messages" / "backup-supervisor-latest.md"
INTAKE_DIR = ROOT / "intake" / "chatgpt"
MAX_PATCHES_PER_RUN = 2
_SAFE_ID = re.compile(r"[^A-Za-z0-9_.-]+")


def supervisor_adapter(*, env: Mapping[str, str] | None = None):
    values = os.environ if env is None else env
    adapters = [make_adapter(n, env=values) for n in SUPERVISOR_ORDER if values.get(PROVIDER_ENV[n], "").strip()]
    return FailoverAdapter(adapters) if adapters else None


def ci_status(repo: str | None, token: str | None, fetch=None) -> dict[str, Any]:
    if not repo or not token:
        return {"available": False, "reason": "no GITHUB_REPOSITORY/GITHUB_TOKEN"}
    url = f"https://api.github.com/repos/{repo}/actions/runs?branch=main&per_page=20"
    try:
        if fetch is None:
            req = Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
            with urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        else:
            data = fetch(url)
    except Exception as exc:  # CI status is informational; never crash
        return {"available": False, "reason": type(exc).__name__}
    latest: dict[str, dict[str, Any]] = {}
    for run in data.get("workflow_runs") or []:
        name = run.get("name") or "?"
        if name not in latest and run.get("status") == "completed":
            latest[name] = {"conclusion": run.get("conclusion"), "id": run.get("id")}
    failing = sorted(n for n, r in latest.items() if r["conclusion"] not in ("success", "skipped", "neutral"))
    return {"available": True, "workflows": len(latest), "failing": failing}


def open_messages() -> list[dict[str, Any]]:
    try:
        from scripts import desk_bridge
        return desk_bridge.open_backlog_rows()
    except Exception:
        return []


def _patch_job(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"backup-supervisor-{item['id']}",
        "project": "workspace",
        "objective": (
            "Produce a minimal unified git diff (paths relative to repo root, a/ b/ prefixes) that completes "
            f"this handoff task: {item['task']}\nEvidence: {item.get('evidence', '')}\n"
            "Allowed paths: scripts/, tests/, knowledge/, messages/, docs/. Never touch .github/, PayoutLens, "
            "secrets or credentials. Put the diff text in `recommendation`; if the task is not small and safe, "
            "set recommendation to an empty string and explain in next_action."
        ),
        "evidence_requirements": [],
    }


def _extract_diff(text: str) -> str:
    text = text.strip()
    fence = re.search(r"```(?:diff|patch)?\n(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    return text + "\n" if text.startswith(("diff --git", "--- ")) else ""


def check_patch(diff: str, repo: Path) -> list[str]:
    problems: list[str] = []
    if not diff:
        return ["empty"]
    if len(diff.encode("utf-8")) > MAX_PATCH_BYTES:
        problems.append("too_large")
    paths = patch_paths(diff)
    if not paths:
        problems.append("no_paths")
    problems += path_blockers(paths)
    if re.search(r"(xai-|sk-|AIza)[A-Za-z0-9_-]{20,}", diff):
        problems.append("secret_like_content")
    if not problems:
        proc = subprocess.run(["git", "apply", "--check", "-"], input=diff, text=True, cwd=repo,
                              capture_output=True)
        if proc.returncode != 0:
            problems.append("git_apply_check_failed")
    return problems


def run(*, env: Mapping[str, str] | None = None, root: Path = ROOT, adapter=None, ci=None,
        messages=None, now: datetime | None = None) -> dict[str, Any]:
    values = os.environ if env is None else env
    current = now or datetime.now(timezone.utc)
    data = handoff.load(root / "state" / "handoffs.json")
    overdue = [i["id"] for i in handoff.overdue(data, at=current)]
    open_items = [i for i in data["items"] if i["status"] in ("open", "claimed")]
    ci = ci if ci is not None else ci_status(values.get("GITHUB_REPOSITORY"), values.get("GITHUB_TOKEN"))
    msgs = messages if messages is not None else open_messages()
    adapter = adapter if adapter is not None else supervisor_adapter(env=values)
    report: dict[str, Any] = {
        "generated_at": current.replace(microsecond=0).isoformat(),
        "provider_available": adapter is not None,
        "overdue": overdue,
        "open_handoffs": [i["id"] for i in open_items],
        "open_messages": len(msgs),
        "ci": ci,
        "patches": [],
        "rejected": [],
    }
    if adapter is not None:
        candidates = [i for i in data["items"] if i["status"] == "open" and i.get("supervisor_ok") is True]
        for item in candidates[:MAX_PATCHES_PER_RUN]:
            target = root / "intake" / "chatgpt" / f"backup-supervisor-{_SAFE_ID.sub('-', item['id'])}.patch"
            if target.exists():
                continue
            try:
                result = adapter.run(_patch_job(item))
            except (MissingCredential, WorkerError) as exc:
                report["rejected"].append({"id": item["id"], "reason": type(exc).__name__})
                continue
            diff = _extract_diff(str(result.get("recommendation") or ""))
            problems = check_patch(diff, root)
            if problems:
                report["rejected"].append({"id": item["id"], "reason": ",".join(problems)})
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(diff, encoding="utf-8")
            report["patches"].append({"id": item["id"], "path": str(target.relative_to(root)),
                                      "provider": result.get("provider")})
    write_status(report, root / "messages" / "backup-supervisor-latest.md")
    return report


def write_status(report: dict[str, Any], path: Path) -> None:
    ci = report["ci"]
    ci_line = (f"{ci['workflows']} workflow, başarısız: {', '.join(ci['failing']) or 'yok'}"
               if ci.get("available") else f"okunamadı ({ci.get('reason')})")
    lines = [
        "# Yedek denetçi (backup-supervisor) — son durum",
        "",
        f"- Zaman (UTC): {report['generated_at']}",
        "- Sağlayıcı: " + ("var (gemini → deepseek → claude → openai)" if report["provider_available"]
                           else "anahtar yok, model adımı atlandı"),
        f"- Gecikmiş handoff (>2 sa açık): {', '.join(report['overdue']) or 'yok'}",
        f"- Açık/claimed handoff: {', '.join(report['open_handoffs']) or 'yok'}",
        f"- Açık masa mesajı: {report['open_messages']}",
        f"- CI (main): {ci_line}",
        f"- Üretilen yama (inceleme için intake/chatgpt/): "
        + (", ".join(p["path"] for p in report["patches"]) or "yok"),
        f"- Reddedilen: " + (", ".join(f"{r['id']} ({r['reason']})" for r in report["rejected"]) or "yok"),
        "",
        "Not: Denetçi main'deki koda doğrudan yazmaz; yamalar chatgpt-intake doğrulamasından ve insan/ajan "
        "incelemesinden geçer. .github/, secret ve PayoutLens'e dokunmaz.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.parse_args(argv)
    report = run()
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
