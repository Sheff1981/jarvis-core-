import unittest
from jarvis.model_registry import ModelCard, ModelRegistry
from jarvis.model_evaluation import Evaluation
from jarvis.neural_backends import CallableAdapter
from jarvis.neural_model_controller import NeuralModelController
from jarvis.neural_runtime import NeuralRuntime
from jarvis.resource_governor import ResourceGovernor
from jarvis.model_lifecycle import ModelState

class NeuralFailureTests(unittest.TestCase):
    def test_recovery_after_backend_exception(self):
        registry = ModelRegistry()
        registry.register(ModelCard("chat", "1", "text", "local", "local:1", 10))
        controller = NeuralModelController(registry, ResourceGovernor(32))
        self.assertTrue(controller.prepare("chat", "1"))
        controller.mark_ready("chat", "1")
        self.assertTrue(controller.activate("chat", "1", Evaluation(20, 20, 0)))
        runtime = NeuralRuntime(controller)
        def fail(prompt):
            raise RuntimeError("unavailable")
        runtime.attach("chat", "1", CallableAdapter(fail))
        with self.assertRaises(RuntimeError):
            runtime.infer("chat", "hello")
        self.assertEqual(controller.lifecycle.state(("chat", "1")), ModelState.READY)
        runtime.attach("chat", "1", CallableAdapter(lambda text: text))
        self.assertEqual(runtime.infer("chat", "ok").text, "ok")
