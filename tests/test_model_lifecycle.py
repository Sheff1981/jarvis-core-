import unittest

from jarvis.model_lifecycle import ModelLifecycle, ModelState
from jarvis.resource_governor import ResourceGovernor


class ModelLifecycleTests(unittest.TestCase):
    def test_full_lifecycle(self):
        governor = ResourceGovernor(100)
        lifecycle = ModelLifecycle(governor)
        self.assertTrue(lifecycle.begin_load("model-v1", 60))
        lifecycle.ready("model-v1")
        lifecycle.acquire("model-v1")
        with self.assertRaises(RuntimeError):
            lifecycle.begin_evict("model-v1")
        lifecycle.release("model-v1")
        lifecycle.begin_evict("model-v1")
        lifecycle.finish_evict("model-v1")
        self.assertEqual(lifecycle.state("model-v1"), ModelState.IDLE)
        self.assertEqual(governor.snapshot()["reserved_mb"], 0)

    def test_budget_denied(self):
        lifecycle = ModelLifecycle(ResourceGovernor(10))
        self.assertFalse(lifecycle.begin_load("large", 20))
        self.assertEqual(lifecycle.state("large"), ModelState.IDLE)

    def test_invalid_transition(self):
        lifecycle = ModelLifecycle(ResourceGovernor(100))
        with self.assertRaises(RuntimeError):
            lifecycle.ready("unknown")


if __name__ == "__main__":
    unittest.main()
