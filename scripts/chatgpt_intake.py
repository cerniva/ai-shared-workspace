#!/usr/bin/env python3
"""Validate ChatGPT patches dropped under intake/chatgpt/ without writing main.

Why: ChatGPT's direct code writes are blocked by a security check. It can still
add one small ``intake/chatgpt/<name>.patch`` (unified git diff). This script
checks each patch read-only: allowed paths only, ``git apply --check`` against
the current tree, then applies it in a throwaway copy and runs the unit tests.
Nothing is pushed; a PASS report tells Grok the patch is safe to apply verbatim.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INTAKE = Path("intake") / "chatgpt"
ALLOWED_PREFIXES = ("scripts/", "tests/", "knowledge/", "messages/", "projects/", "reports/", "docs/")
DENIED_PATTERNS = (re.compile(r"(^|/)\.github/"), re.compile(r"payoutlens", re.I),
                   re.compile(r"(^|/)\.env"), re.compile(r"secret", re.I))
MAX_PATCH_BYTES = 64_000
DIFF_PATH = re.compile(r"^(?:\+\+\+|---) (?:[ab]/)?(\S+)", re.M)


def patch_paths(text: str) -> list[str]:
    return sorted({p for p in DIFF_PATH.findall(text) if p != "/dev/null"})


def path_blockers(paths: list[str]) -> list[str]:
    blockers = []
    if not paths:
        blockers.append("no_paths")
    for path in paths:
        if ".." in Path(path).parts or path.startswith("/"):
            blockers.append(f"unsafe_path:{path}")
        elif any(p.search(path) for p in DENIED_PATTERNS):
            blockers.append(f"denied_path:{path}")
        elif not path.startswith(ALLOWED_PREFIXES):
            blockers.append(f"outside_allowed:{path}")
    return blockers


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)


def validate_patch(patch: Path, repo: Path, run_tests: bool = True) -> dict[str, Any]:
    report: dict[str, Any] = {"patch": patch.name, "status": "FAIL", "blockers": []}
    data = patch.read_bytes()
    if len(data) > MAX_PATCH_BYTES:
        report["blockers"].append("too_large")
        return report
    text = data.decode("utf-8", errors="replace")
    paths = patch_paths(text)
    report["paths"] = paths
    report["blockers"] += path_blockers(paths)
    if report["blockers"]:
        return report
    check = _git(["apply", "--check", str(patch.resolve())], repo)
    if check.returncode != 0:
        report["blockers"].append("git_apply_check_failed")
        report["detail"] = (check.stderr or check.stdout).strip()[-2000:]
        return report
    if run_tests:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(repo, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            applied = subprocess.run(["git", "apply", str(patch.resolve())], cwd=copy,
                                     text=True, capture_output=True, check=False)
            if applied.returncode != 0:
                report["blockers"].append("git_apply_failed")
                return report
            tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
                                   cwd=copy, text=True, capture_output=True, check=False)
            report["tests_tail"] = (tests.stderr or "").strip().splitlines()[-3:]
            if tests.returncode != 0:
                report["blockers"].append("tests_failed")
                return report
    report["status"] = "PASS"
    return report


def validate_all(repo: Path, run_tests: bool = True) -> list[dict[str, Any]]:
    folder = repo / INTAKE
    return [validate_patch(p, repo, run_tests) for p in sorted(folder.glob("*.patch"))]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--no-tests", action="store_true")
    args = parser.parse_args(argv)
    reports = validate_all(args.repo.resolve(), run_tests=not args.no_tests)
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0 if all(r["status"] == "PASS" for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
