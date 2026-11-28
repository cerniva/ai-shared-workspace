"""Emit a source-linked Finance altseason decision as a read-back-verified JSON artifact.

This is an opt-in local producer, not a claim that the scheduled Finance report
has consumed the artifact. It uses the real altseason_panel decision gate.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path

from projects.finance.altcoin_panel import altseason_panel


def produce(values_path: Path, output_path: Path) -> dict:
    # Never replace the raw input artifact, including through a symlink alias.
    if Path(values_path).resolve() == Path(output_path).resolve():
        raise ValueError("bridge_failure: finance output must not overwrite input")
    values = json.loads(Path(values_path).read_text(encoding="utf-8"))
    if not isinstance(values, dict) or any(
        not isinstance(k, str) or
        (v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))
                            or not math.isfinite(v)))
        for k, v in values.items()
    ):
        raise ValueError("finance input must be a map of finite numeric or null values")

    # This must fail before output creation if the active, source-linked
    # finance learning is missing, duplicated or no longer matches policy.
    decision = altseason_panel(values)
    if not decision.get("applied_learning_ids"):
        raise ValueError("bridge_failure: finance decision did not apply a learning")

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(decision, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    if json.loads(target.read_text(encoding="utf-8")) != decision:
        raise OSError("bridge_failure: finance artifact read-back mismatch")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--values-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    produce(args.values_json, args.output_json)


if __name__ == "__main__":
    main()
