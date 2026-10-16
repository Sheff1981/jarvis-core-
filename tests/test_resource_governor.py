"""Regression tests for conservative Neural Core memory admission."""
import unittest

from jarvis.resource_governor import ResourceGovernor


class ResourceGovernorTests(unittest.TestCase):
    def test_budget_and_release(self):
        governor = ResourceGovernor(budget_mb=100)
        first = governor.reserve("indexer", 80)
        self.assertIsNotNone(first)
        self.assertIsNone(governor.reserve("trainer", 30))
        self.assertEqual(governor.snapshot()["available_mb"], 20)
        governor.release(first)
        self.assertEqual(governor.snapshot()["available_mb"], 100)

    def test_rejects_stale_reservation(self):
        governor = ResourceGovernor(100)
        first = governor.reserve("indexer", 20)
        governor.release(first)
        with self.assertRaises(ValueError):
            governor.release(first)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            ResourceGovernor(0)
        governor = ResourceGovernor()
        with self.assertRaises(ValueError):
            governor.reserve("", 10)
        with self.assertRaises(ValueError):
            governor.reserve("indexer", 0)

    def test_separate_owners(self):
        governor = ResourceGovernor(100)
        first = governor.reserve("memory", 40)
        second = governor.reserve("evaluation", 50)
        self.assertEqual(governor.snapshot()["active_reservations"], 2)
        governor.release(first)
        self.assertEqual(governor.snapshot()["available_mb"], 50)
        governor.release(second)
        self.assertEqual(governor.snapshot()["reserved_mb"], 0)


if __name__ == "__main__":
    unittest.main()
