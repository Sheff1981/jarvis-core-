"""Small neural intent model tests."""
import tempfile
import unittest
from pathlib import Path

from jarvis.intent_network import IntentNetwork


DATA = [
    ("открой браузер", "open"), ("запусти браузер", "open"),
    ("открой программу", "open"), ("запусти программу", "open"),
    ("закрой браузер", "close"), ("останови браузер", "close"),
    ("закрой программу", "close"), ("останови программу", "close"),
]


class IntentNetworkTests(unittest.TestCase):
    def test_cpu_training_and_reload(self):
        model = IntentNetwork.train(DATA, epochs=120)
        self.assertEqual(model.predict("открой браузер")["label"], "open")
        self.assertEqual(model.predict("закрой программу")["label"], "close")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "intent.json"
            model.save(path)
            loaded = IntentNetwork.load(path)
            self.assertEqual(loaded.predict("закрой программу"), model.predict("закрой программу"))

    def test_unknown_input_is_not_confident(self):
        model = IntentNetwork.train(DATA)
        self.assertEqual(model.predict("неизвестное слово")["confidence"], 0.0)

    def test_requires_labeled_data(self):
        with self.assertRaises(ValueError):
            IntentNetwork.train([("текст", "one")])
        with self.assertRaises(ValueError):
            IntentNetwork.train([("a", "same")] * 4)


if __name__ == "__main__":
    unittest.main()
