import unittest

from jarvis.model_evaluation import Evaluation
from jarvis.model_registry import ModelCard, ModelRegistry
from jarvis.safe_model_promotion import SafeModelPromotion


class SafePromotionTests(unittest.TestCase):
    def test_reject_then_promote_and_rollback(self):
        registry = ModelRegistry()
        for version in ("v1", "v2"):
            registry.register(ModelCard("intent", version, "classifier", "onnx",
                                        "models/" + version, 20))
        registry.promote("intent", "v1")
        guard = SafeModelPromotion(registry)
        self.assertFalse(guard.promote("intent", "v2", Evaluation(20, 12, 0)))
        self.assertEqual(registry.get("intent").version, "v1")
        self.assertTrue(guard.promote("intent", "v2", Evaluation(20, 20, 0)))
        self.assertEqual(registry.get("intent").version, "v2")
        guard.rollback("intent")
        self.assertEqual(registry.get("intent").version, "v1")

    def test_unknown_version_rejected(self):
        registry = ModelRegistry()
        with self.assertRaises(KeyError):
            SafeModelPromotion(registry).promote("unknown", "v1", Evaluation(20, 20, 0))


if __name__ == "__main__":
    unittest.main()
