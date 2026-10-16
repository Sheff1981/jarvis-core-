"""Neural Core contour integration and concurrency safety."""
import unittest

from jarvis.model_registry import ModelCard, ModelRegistry
from jarvis.neural_backends import CallableAdapter
from jarvis.neural_model_controller import NeuralModelController
from jarvis.neural_runtime import NeuralRuntime
from jarvis.resource_governor import ResourceGovernor
from jarvis.model_evaluation import Evaluation


class NeuralContourTests(unittest.TestCase):
    def setUp(self):
        self.registry = ModelRegistry()
        for version in ("1", "2"):
            self.registry.register(ModelCard("dialogue", version, "text", "local",
                                             "local:" + version, 20))
        self.controller = NeuralModelController(self.registry, ResourceGovernor(64))
        self.runtime = NeuralRuntime(self.controller)
        for version in ("1", "2"):
            self.assertTrue(self.controller.prepare("dialogue", version))
            self.controller.mark_ready("dialogue", version)
            self.runtime.attach("dialogue", version,
                                CallableAdapter(lambda text, v=version: v + ":" + text))
        self.evaluation = Evaluation(total=20, passed=20, errors=0)

    def test_active_inference_and_rollback(self):
        self.assertTrue(self.controller.activate("dialogue", "1", self.evaluation))
        self.assertEqual(self.runtime.infer("dialogue", "hello").text, "1:hello")
        self.assertTrue(self.controller.activate("dialogue", "2", self.evaluation))
        self.assertEqual(self.runtime.infer("dialogue", "hello").text, "2:hello")
        self.controller.rollback("dialogue")
        self.assertEqual(self.runtime.infer("dialogue", "hello").text, "1:hello")

    def test_no_active_unload_or_detach(self):
        self.controller.activate("dialogue", "1", self.evaluation)
        with self.assertRaises(RuntimeError):
            self.controller.unload("dialogue", "1")
        with self.assertRaises(RuntimeError):
            self.runtime.detach("dialogue", "1")

    def test_busy_model_cannot_be_unloaded(self):
        self.controller.activate("dialogue", "1", self.evaluation)
        def during_inference(prompt):
            with self.assertRaises(RuntimeError):
                self.controller.unload("dialogue", "2") if False else self.controller.unload("dialogue", "1")
            return prompt
        self.runtime.attach("dialogue", "1", CallableAdapter(during_inference))
        self.assertEqual(self.runtime.infer("dialogue", "ok").text, "ok")

    def test_unattached_backend_rejected(self):
        self.controller.activate("dialogue", "1", self.evaluation)
        self.runtime._adapters.pop(("dialogue", "1"))
        with self.assertRaises(RuntimeError):
            self.runtime.infer("dialogue", "hello")


if __name__ == "__main__":
    unittest.main()
