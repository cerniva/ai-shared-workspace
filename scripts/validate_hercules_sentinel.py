from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from hercules_sentinel.contract import load_contract
from hercules_sentinel.evaluator import evaluate_report


def _read_object(path: Path, label: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return data


def _error_result(message: str) -> dict[str, Any]:
    return {
        "valid": False,
        "duplicate": False,
        "forbidden": False,
        "errors": [message],
        "event_fingerprint": "",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Hercules Sentinel pilot report")
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--event", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--seen-fingerprint", action="append", default=[])
    args = parser.parse_args(argv)

    try:
        contract = load_contract(args.contract)
        event = _read_object(args.event, "event")
        report = _read_object(args.report, "report")
        result = evaluate_report(report, event, set(args.seen_fingerprint), contract)
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        result = _error_result("invalid or unreadable JSON input")

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("valid") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
