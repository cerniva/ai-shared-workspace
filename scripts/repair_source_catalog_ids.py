from __future__ import annotations

import json
from pathlib import Path

from scripts.knowledge_bridge import normalize_record


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "knowledge" / "source_catalog.json"


def main() -> int:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    normalized = [normalize_record(item) for item in data["sources"]]

    ids = [item["source_id"] for item in normalized]
    canonicals = [item["canonical"] for item in normalized]
    if len(ids) != len(set(ids)) or len(canonicals) != len(set(canonicals)):
        raise RuntimeError("duplicate source after canonical normalization")

    normalized.sort(key=lambda item: item["source_id"])
    data["sources"] = normalized
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
