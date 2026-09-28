from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.knowledge_bridge import DEFAULT_CATALOG, SourceCatalog
from scripts.learning_bridge import DEFAULT_LEDGER, LearningLedger


CORE05_DOMAIN = "CORE-05"


class Core05KnowledgeAdapter:
    """Thin CORE-05 adapter over the shared source and learning bridges."""

    def __init__(
        self,
        catalog_path: str | Path = DEFAULT_CATALOG,
        ledger_path: str | Path = DEFAULT_LEDGER,
    ) -> None:
        """Bind CORE-05 to trusted shared catalog and ledger paths."""
        self.catalog = SourceCatalog(catalog_path)
        self.ledger = LearningLedger(ledger_path, catalog_path)

    def record_source(self, record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Persist a source through the shared catalog with its safeguards."""
        return self.catalog.add(record)

    def record_learning(self, record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Persist a source-linked learning while forcing the CORE-05 domain."""
        payload = dict(record)
        payload["domain"] = CORE05_DOMAIN
        return self.ledger.add(payload)

    def read_source(self, value: str) -> dict[str, Any] | None:
        """Read a source by stable source ID or canonical source value."""
        return self.catalog.find(value)

    def read_learning(self, learning_id: str) -> dict[str, Any] | None:
        """Read a learning only when it belongs to the CORE-05 domain."""
        item = self.ledger.find(learning_id)
        if item is None or item.get("domain") != CORE05_DOMAIN:
            return None
        return item

    def validate(self) -> dict[str, int | bool]:
        """Validate both shared stores and return their current record counts."""
        return {
            "valid": True,
            "source_count": self.catalog.validate(),
            "learning_count": self.ledger.validate(),
        }
