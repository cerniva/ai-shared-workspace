import unittest

from runtime.policy import classify_task


class PolicyTests(unittest.TestCase):
    def test_allows_only_synthetic_echo_read_or_prepare(self):
        for action_class in ("read", "prepare"):
            decision = classify_task({"connector": "synthetic", "operation": "echo", "action_class": action_class})
            self.assertTrue(decision.allowed)

    def test_unknown_pair_is_blocked(self):
        decision = classify_task({"connector": "shopify", "operation": "write", "action_class": "prepare"})
        self.assertFalse(decision.allowed)

    def test_high_impact_class_is_blocked_even_with_safe_name(self):
        decision = classify_task({"connector": "synthetic", "operation": "echo", "action_class": "payment"})
        self.assertFalse(decision.allowed)


if __name__ == "__main__":
    unittest.main()
