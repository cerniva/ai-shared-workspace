#!/usr/bin/env python3
"""Fail closed on GitHub cross-run render ZIP digest before upload consumes it."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import quote
from urllib.request import Request, urlopen
import zipfile

from scripts.knowledge_bridge import SourceCatalog, DEFAULT_CATALOG
from scripts.learning_bridge import LearningLedger, DEFAULT_LEDGER

LEARNING_ID = "learn_4decad368966e2e6"
SOURCE_ID = "src_569c596da7048714"
MAX_UNCOMPRESSED = 2 * 1024**3


def active_rule(ledger=DEFAULT_LEDGER, catalog=DEFAULT_CATALOG):
    rows = LearningLedger(ledger, catalog).for_plan("system")
    matches = [row for row in rows if row.get("learning_id") == LEARNING_ID
               and row.get("status", "active") == "active"]
    if len(matches) != 1 or SOURCE_ID not in matches[0].get("source_ids", []):
        raise ValueError("bridge_failure: active system digest learning missing or superseded")
    if "digest mismatch" not in matches[0].get("decision", ""):
        raise ValueError("bridge_failure: digest learning decision changed")
    source = SourceCatalog(catalog).find(SOURCE_ID)
    if not source or source.get("evidence_tier") != "official":
        raise ValueError("bridge_failure: official artifact digest source missing")
    return {"learning_id": LEARNING_ID, "source_ids": [SOURCE_ID]}


def verify_and_extract(archive: Path, digest: str, destination: Path):
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("bridge_failure: artifact metadata digest missing or malformed")
    h = hashlib.sha256()
    with archive.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    if h.hexdigest() != digest.split(":", 1)[1]:
        raise ValueError("bridge_failure: cross-run artifact digest mismatch")
    if destination.exists():
        raise ValueError("bridge_failure: destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="render-verified-", dir=destination.parent))
    try:
        with zipfile.ZipFile(archive) as zf:
            seen = set()
            total = 0
            for info in zf.infolist():
                name = info.filename
                parts = PurePosixPath(name).parts
                if not name or name.startswith("/") or "\\" in name or ".." in parts or name in seen:
                    raise ValueError("bridge_failure: unsafe or duplicate ZIP path")
                seen.add(name)
                if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                    raise ValueError("bridge_failure: ZIP symlink not allowed")
                total += info.file_size
                if total > MAX_UNCOMPRESSED:
                    raise ValueError("bridge_failure: artifact uncompressed size exceeds cap")
            zf.extractall(stage)
        if not (stage / "preflight.json").is_file() or not (stage / "bundle" / "render.json").is_file():
            raise ValueError("bridge_failure: render artifact lacks required evidence")
        stage.rename(destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def fetch_metadata(repo: str, run_id: int, name: str, token: str):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("bridge_failure: invalid GitHub repository")
    if run_id < 1 or not re.fullmatch(r"[A-Za-z0-9._-]{1,120}", name):
        raise ValueError("bridge_failure: invalid run or artifact name")
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100&name={quote(name)}"
    req = Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=30) as response:
        data = json.load(response)
    matches = [a for a in data.get("artifacts", []) if a.get("name") == name and not a.get("expired")]
    if len(matches) != 1:
        raise ValueError("bridge_failure: expected one non-expired artifact for requested run")
    artifact = matches[0]
    expected_url = f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact['id']}/zip"
    if artifact.get("archive_download_url") != expected_url:
        raise ValueError("bridge_failure: unexpected artifact download URL")
    return artifact


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--name", required=True)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--consumer", choices=["youtube-upload.yml:render_artifact", "verify-render-artifact-only.yml:read_only"], default="youtube-upload.yml:render_artifact")
    args = parser.parse_args(argv)
    try:
        evidence = active_rule()
        repo = os.environ["GITHUB_REPOSITORY"]
        token = os.environ["GITHUB_TOKEN"]
        artifact = fetch_metadata(repo, args.run_id, args.name, token)
        digest = artifact.get("digest", "")
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "render.zip"
            result = subprocess.run([
                "curl", "--fail", "--silent", "--show-error", "--location", "--retry", "0",
                "--header", f"Authorization: Bearer {token}",
                "--header", "Accept: application/vnd.github+json",
                "--output", str(archive), artifact["archive_download_url"],
            ], check=False, timeout=180)
            if result.returncode != 0:
                raise ValueError(f"bridge_failure: artifact download failed exit={result.returncode}")
            verify_and_extract(archive, digest, args.destination)
        report = {
            "status": "PASS", "consumer": args.consumer,
            "run_id": args.run_id, "artifact_id": artifact["id"], "artifact_digest": digest,
            "decision_before": "reject_unverified_cross_run_artifact",
            "decision_after": "accept_digest_verified_cross_run_artifact",
            "applied_learning_ids": [evidence["learning_id"]], "source_ids": evidence["source_ids"],
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
        if json.loads(args.report.read_text(encoding="utf-8")) != report:
            raise ValueError("bridge_failure: report read-back mismatch")
        print(json.dumps(report, sort_keys=True))
        return 0
    except subprocess.TimeoutExpired:
        print("bridge_failure: artifact download timed out", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"bridge_failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
