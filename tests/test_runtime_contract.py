import unittest

from scripts.runtime_contract import idempotency_key, validate_dispatch_document, validate_dispatch_item


class RuntimeContractTests(unittest.TestCase):
    def test_empty_v1_document_validates(self):
        self.assertEqual(validate_dispatch_document({"version": 1, "items": []}), [])

    def test_required_fields_are_enforced(self):
        errors = validate_dispatch_item({})
        for field in ("id", "generation", "task_type", "connector", "operation", "action_class", "params", "created_at"):
            self.assertTrue(any(field in error for error in errors), field)

    def test_future_version_is_rejected(self):
        errors = validate_dispatch_document({"version": 2, "items": []})
        self.assertTrue(errors)

    def test_write_low_risk_is_rejected_in_v1(self):
        item = self._valid_item()
        item["action_class"] = "write-low-risk"
        self.assertTrue(validate_dispatch_item(item))

    def test_idempotency_key_uses_id_and_generation(self):
        self.assertEqual(idempotency_key({"id": "A", "generation": 2}), "A:2")

    def test_unknown_connector_operation_pair_is_rejected(self):
        item = self._valid_item()
        item["connector"] = "unknown"
        item["operation"] = "noop"
        self.assertTrue(validate_dispatch_item(item))

    @staticmethod
    def _valid_item():
        return {
            "id": "RUNTIME-SMOKE-1",
            "generation": 1,
            "task_type": "synthetic",
            "connector": "synthetic",
            "operation": "echo",
            "action_class": "prepare",
            "params": {"message": "hello"},
            "created_at": "2026-09-27T00:00:00Z",
        }


if __name__ == "__main__":
    unittest.main()
