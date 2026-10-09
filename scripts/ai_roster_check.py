#!/usr/bin/env python3
"""AI roster check: per provider report configured/missing (env names only)
and, when configured, one tiny live test call. Never prints secret values and
never crashes on a missing key or provider error; writes a JSON artifact."""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.provider_config import PROVIDER_ENV, credential_status, make_adapter  # noqa: E402
from scripts.worker_adapters import MissingCredential, ProviderAuthError, WorkerError  # noqa: E402

PING_JOB = {
    "id": "ai-roster-ping",
    "project": "workspace",
    "objective": "Roster health ping. Reply with the JSON object; keep every field minimal "
                 "(empty arrays, recommendation 'ok', confidence 1, next_action 'none').",
    "evidence_requirements": [],
}


def check(*, env: Mapping[str, str] | None = None, live: bool = True, factory=make_adapter) -> dict[str, Any]:
    status = credential_status(env=env)
    providers: dict[str, Any] = {}
    for name, info in status.items():
        entry: dict[str, Any] = dict(info)
        if info["status"] != "configured":
            entry["test_call"] = "skipped_missing_credential"
        elif not live:
            entry["test_call"] = "skipped_dry_run"
        else:
            try:
                result = factory(name, env=env).run(dict(PING_JOB))
                entry["test_call"] = "ok"
                entry["model"] = result.get("model")
                entry["duration_ms"] = result.get("timing", {}).get("duration_ms")
                if name == "perplexity":
                    entry["citations_count"] = len(result.get("citations") or [])
            except MissingCredential:
                entry["test_call"] = "skipped_missing_credential"
            except ProviderAuthError as exc:
                entry["test_call"] = "auth_error"
                entry["http_status"] = exc.http_status
                entry["error_code"] = exc.error_code
            except WorkerError as exc:
                entry["test_call"] = "error"
                entry["error_class"] = type(exc).__name__
                entry["error"] = str(exc)[:200]
            except Exception as exc:  # never crash the roster
                entry["test_call"] = "error"
                entry["error_class"] = type(exc).__name__
        providers[name] = entry
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "providers": providers,
        "configured": sorted(n for n, e in providers.items() if e["status"] == "configured"),
        "missing_secrets": sorted(PROVIDER_ENV[n] for n, e in providers.items() if e["status"] == "missing"),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path, default=Path("ai-roster.json"))
    p.add_argument("--dry-run", action="store_true", help="names-only, no live calls")
    args = p.parse_args(argv)
    report = check(live=not args.dry_run)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, e in report["providers"].items():
        print(f"{name:11s} {e['env']:20s} {e['status']:10s} {e['test_call']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
