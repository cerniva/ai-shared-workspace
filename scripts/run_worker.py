from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.provider_config import make_adapter
from scripts.work_queue import WorkQueue
from scripts.worker_adapters import MockAdapter
from scripts.worker_runner import run_job


def execute(argv: Sequence[str] | None = None, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Run one queued AI worker job")
    parser.add_argument("--job", required=True)
    parser.add_argument("--provider", choices=["openai", "grok", "gemini"], required=True)
    parser.add_argument("--queue", default="state/work_queue.json")
    parser.add_argument("--dead-letter", default="state/dead_letter.json")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args(argv)

    values = os.environ if env is None else env
    if args.mock:
        adapter = MockAdapter(provider=args.provider, model=f"mock-{args.provider}")
    else:
        adapter = make_adapter(args.provider, env=values)

    return run_job(
        WorkQueue(Path(args.queue)),
        args.job,
        adapter,
        worker=args.provider,
        dead_letter_path=Path(args.dead_letter),
    )


def main() -> None:
    state = execute()
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
