"""Persistence regression checks for versioned model registry."""
import json
import tempfile
from pathlib import Path
import unittest

from jarvis.model_registry import ModelCard, ModelRegistry
from jarvis.model_registry_storage import load_registry, save_registry


class ModelRegistryStorageTests(unittest.TestCase):
    def test_round_trip_with_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            registry = ModelRegistry()
            registry.register(ModelCard("intent", "v1", "classifier", "onnx", "models/v1", 20))
            registry.register(ModelCard("intent", "v2", "classifier", "onnx", "models/v2", 24))
            registry.promote("intent", "v1")
            registry.promote("intent", "v2")
            save_registry(registry, path)
            restored = load_registry(path)
            self.assertEqual(restored.get("intent").version, "v2")
            self.assertEqual(restored.rollback("intent").version, "v1")

    def test_invalid_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text('{"schema": 99, "models": []}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_registry(path)

    def test_invalid_active_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps({
                "schema": 1, "models": [], "active": {"intent": "missing"},
                "previous": {}
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_registry(path)


if __name__ == "__main__":
    unittest.main()
