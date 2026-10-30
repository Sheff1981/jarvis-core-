"""Regression tests for model version activation and rollback."""
import unittest

from jarvis.model_registry import ModelCard, ModelRegistry


def card(version):
    return ModelCard("intent", version, "classifier", "onnx", "models/intent", 25)


class ModelRegistryTests(unittest.TestCase):
    def test_activation_and_rollback(self):
        registry = ModelRegistry()
        registry.register(card("v1"))
        registry.register(card("v2"))
        registry.promote("intent", "v1")
        registry.promote("intent", "v2")
        self.assertEqual(registry.get("intent").version, "v2")
        self.assertEqual(registry.rollback("intent").version, "v1")
        self.assertEqual(registry.get("intent").version, "v1")

    def test_duplicate_version(self):
        registry = ModelRegistry()
        registry.register(card("v1"))
        with self.assertRaises(ValueError):
            registry.register(card("v1"))

    def test_unknown_model(self):
        registry = ModelRegistry()
        with self.assertRaises(KeyError):
            registry.promote("missing", "v1")
        with self.assertRaises(KeyError):
            registry.rollback("missing")

    def test_noop_promotion(self):
        registry = ModelRegistry()
        registry.register(card("v1"))
        self.assertTrue(registry.promote("intent", "v1"))
        self.assertFalse(registry.promote("intent", "v1"))

    def test_invalid_memory_estimate(self):
        registry = ModelRegistry()
        with self.assertRaises(ValueError):
            registry.register(ModelCard("intent", "v1", "classifier", "onnx", "x", 0))


if __name__ == "__main__":
    unittest.main()
