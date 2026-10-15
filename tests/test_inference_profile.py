import unittest
from jarvis.inference_profile import InferenceProfile


class InferenceProfileTests(unittest.TestCase):
    def test_defaults_suit_cpu(self):
        profile = InferenceProfile()
        self.assertEqual(profile.model, "qwen2.5:1.5b")
        self.assertEqual(profile.history_limit, 6)
        self.assertEqual(profile.ollama_options()["num_ctx"], 2048)
        self.assertEqual(profile.ollama_options()["num_predict"], 160)

    def test_reject_bad_limits(self):
        for kwargs in ({"history_limit": 101}, {"num_ctx": 0},
                       {"num_thread": True}, {"model": ""}):
            with self.assertRaises(ValueError):
                InferenceProfile(**kwargs)


if __name__ == "__main__":
    unittest.main()
