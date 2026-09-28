#!/usr/bin/env python3
"""Build a compact, query-focused context pack from the shared workspace.

Run from a checkout:
  python3 -m scripts.desk_context status
  python3 -m scripts.desk_context search "Grok API 403 credits"
The output is evidence for an agent to inspect; it does not contact agents or
send notifications.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path

from scripts.core05_knowledge_adapter import Core05KnowledgeAdapter

ROOT = Path(__file__).resolve().parents[1]
BASELINE = [
    "DESK.md",
    "state/now.json",
    "tasks/active.json",
    "state/status.json",
]
FIXED_SOURCES = [
    "PROTOCOL.md",
    "README.md",
    "research/KNOWLEDGE_LEDGER.md",
    "messages/team-reports.md",
]
SKIP_PARTS = {"archive", "vendor", "node_modules", ".git"}
MAX_FILE_BYTES = 1_000_000
MAX_EXCERPTS = 7
MAX_LINES_PER_EXCERPT = 8
SECRET_LINE = re.compile(
    r"(?i)(api[_ -]?key|client[_ -]?secret|access[_ -]?token|refresh[_ -]?token|"
    r"authorization\s*[:=]\s*bearer)\s*[:=]\s*\S+"
)
BEARER = re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+/=-]{12,}")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def redact(line: str) -> str:
    if SECRET_LINE.search(line):
        return "[REDACTED: possible secret]"
    return BEARER.sub("Bearer [REDACTED]", line)


def git_revision() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            check=True, capture_output=True, text=True, timeout=2,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown (not a git checkout)"


def candidate_paths() -> list[Path]:
    paths: list[Path] = []
    for relative in BASELINE + FIXED_SOURCES:
        path = ROOT / relative
        if path.is_file():
            paths.append(path)
    for folder in ("tasks", "state", "research", "knowledge", "docs"):
        base = ROOT / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".yaml", ".yml"}:
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.stat().st_size <= MAX_FILE_BYTES:
                paths.append(path)
    # Reports are useful for recent decisions; do not search inbox/raw chat queues.
    report = ROOT / "messages/team-reports.md"
    if report.is_file():
        paths.append(report)
    unique: dict[str, Path] = {}
    for path in paths:
        unique[str(path.relative_to(ROOT))] = path
    return list(unique.values())


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return ""
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def print_header(mode: str) -> None:
    print(f"Repo context | mode={mode} | revision={git_revision()}")
    print("This is a local snapshot; verify cited files before making current-state claims.")


def core05_knowledge_health() -> str:
    """Return fail-closed CORE-05 shared knowledge bridge health for operators."""
    try:
        result = Core05KnowledgeAdapter().validate()
    except Exception as exc:
        return f"CORE-05 knowledge bridge: ERROR ({type(exc).__name__}: {exc})"
    if result.get("valid") is not True:
        return "CORE-05 knowledge bridge: INVALID"
    return (
        "CORE-05 knowledge bridge: VALID "
        f"sources={result['source_count']} learnings={result['learning_count']}"
    )


def status() -> None:
    """Print the current operational baseline plus CORE-05 knowledge health."""
    print_header("status")
    print(core05_knowledge_health())
    for rel in BASELINE:
        path = ROOT / rel
        text = read_text(path)
        if not text:
            continue
        print(f"\n--- {rel} ---")
        if path.suffix == ".json":
            try:
                text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
        lines = text.splitlines()
        for line in lines[:80]:
            print(redact(line))
        if len(lines) > 80:
            print(f"... [{len(lines) - 80} more lines; inspect the file directly]")


def search(query: str) -> None:
    terms = [t for t in re.findall(r"[\w.-]+", normalize(query)) if len(t) >= 3]
    if not terms:
        raise SystemExit("Give a query with at least one searchable word (3+ characters).")
    print_header("search")
    print("Query terms: " + ", ".join(terms))

    # Always surface the small current-state baseline first.
    for rel in ("state/now.json", "tasks/active.json"):
        path = ROOT / rel
        text = read_text(path)
        if text:
            print(f"\n--- current state: {rel} ---")
            lines = text.splitlines()
            for line in lines[:60]:
                print(redact(line))
            if len(lines) > 60:
                print("... [truncated; inspect the file directly]")

    ranked: list[tuple[int, str, list[str]]] = []
    for path in candidate_paths():
        rel = str(path.relative_to(ROOT))
        if rel in {"state/now.json", "tasks/active.json"}:
            continue
        lines = read_text(path).splitlines()
        if not lines:
            continue
        norm = normalize("\n".join(lines))
        score = sum(norm.count(term) for term in terms)
        if score == 0:
            continue
        hits = [i for i, line in enumerate(lines) if any(term in normalize(line) for term in terms)]
        excerpts: list[str] = []
        seen: set[int] = set()
        for i in hits:
            start, end = max(0, i - 1), min(len(lines), i + 2)
            if any(j in seen for j in range(start, end)):
                continue
            seen.update(range(start, end))
            excerpt = "\n".join(f"{j + 1}: {redact(lines[j])}" for j in range(start, end))
            excerpts.append(excerpt)
            if len(excerpts) >= MAX_EXCERPTS:
                break
        ranked.append((score, rel, excerpts))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    if not ranked:
        print("\nNo matching indexed repo files. Search manually before concluding the information is absent.")
        return
    for score, rel, excerpts in ranked[:8]:
        print(f"\n--- match: {rel} (score={score}) ---")
        for excerpt in excerpts:
            print(excerpt)
            print("...")
    if len(ranked) > 8:
        print(f"\n{len(ranked) - 8} more matching files omitted; inspect them if the answer depends on completeness.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="show the current task and state files")
    query_parser = commands.add_parser("search", help="search repo notes for a question")
    query_parser.add_argument("query", nargs="+", help="topic or question to search")
    args = parser.parse_args()
    if args.command == "status":
        status()
    else:
        search(" ".join(args.query))


if __name__ == "__main__":
    main()
