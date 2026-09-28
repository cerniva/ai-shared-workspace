from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from scripts import desk_context


class DeskContextHealthTests(unittest.TestCase):
    """Verify that operator status exposes CORE-05 bridge health safely."""

    @patch("scripts.desk_context.Core05KnowledgeAdapter")
    def test_core05_health_reports_valid_counts(self, adapter_cls) -> None:
        """A valid bridge should expose source and learning counts."""
        adapter_cls.return_value.validate.return_value = {
            "valid": True,
            "source_count": 7,
            "learning_count": 3,
        }
        self.assertEqual(
            desk_context.core05_knowledge_health(),
            "CORE-05 knowledge bridge: VALID sources=7 learnings=3",
        )

    @patch("scripts.desk_context.Core05KnowledgeAdapter")
    def test_core05_health_fails_closed(self, adapter_cls) -> None:
        """Bridge validation errors should be visible instead of faked as healthy."""
        adapter_cls.return_value.validate.side_effect = ValueError("invalid ledger")
        self.assertEqual(
            desk_context.core05_knowledge_health(),
            "CORE-05 knowledge bridge: ERROR (ValueError: invalid ledger)",
        )

    @patch("scripts.desk_context.Core05KnowledgeAdapter")
    @patch("scripts.desk_context.git_revision", return_value="test-sha")
    def test_status_calls_bridge_health(self, _revision, adapter_cls) -> None:
        """The real status entrypoint should call and print bridge validation."""
        adapter_cls.return_value.validate.return_value = {
            "valid": True,
            "source_count": 1,
            "learning_count": 1,
        }
        output = io.StringIO()
        with patch.object(desk_context, "BASELINE", []), redirect_stdout(output):
            desk_context.status()
        self.assertIn(
            "CORE-05 knowledge bridge: VALID sources=1 learnings=1",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
