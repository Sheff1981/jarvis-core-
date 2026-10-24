import unittest

from jarvis.model_evaluation import Evaluation
from jarvis.model_registry import ModelCard, ModelRegistry
from jarvis.neural_model_controller import NeuralModelController
from jarvis.process_memory import current_process_memory
from jarvis.resource_governor import ResourceGovernor


class NeuralModelControllerTests(unittest.TestCase):
    def setUp(self):
        self.registry = ModelRegistry()
        for version in ("v1", "v2"):
            self.registry.register(ModelCard("intent", version, "classifier",
                                             "onnx", "models/" + version, 40))
        self.governor = ResourceGovernor(100)
        self.controller = NeuralModelController(self.registry, self.governor)

    def test_activate_and_rollback(self):
        self.assertTrue(self.controller.prepare("intent", "v1"))
        self.controller.mark_ready("intent", "v1")
        self.assertTrue(self.controller.activate("intent", "v1", Evaluation(20, 20, 0)))
        self.assertTrue(self.controller.prepare("intent", "v2"))
        self.controller.mark_ready("intent", "v2")
        self.assertFalse(self.controller.activate("intent", "v2", Evaluation(20, 5, 0)))
        self.assertTrue(self.controller.activate("intent", "v2", Evaluation(20, 20, 0)))
        self.assertEqual(self.controller.rollback("intent").version, "v1")
        self.controller.unload("intent", "v2")
        self.assertEqual(self.governor.snapshot()["reserved_mb"], 40)

    def test_cannot_unload_active(self):
        self.controller.prepare("intent", "v1")
        self.controller.mark_ready("intent", "v1")
        self.controller.activate("intent", "v1", Evaluation(20, 20, 0))
        with self.assertRaises(RuntimeError):
            self.controller.unload("intent", "v1")

    def test_budget(self):
        self.assertTrue(self.controller.prepare("intent", "v1"))
        self.assertTrue(self.controller.prepare("intent", "v2"))
        self.assertEqual(self.governor.snapshot()["reserved_mb"], 80)

    def test_memory_probe(self):
        result = current_process_memory()
        self.assertTrue(result.rss_bytes is None or result.rss_bytes >= 0)


if __name__ == "__main__":
    unittest.main()
