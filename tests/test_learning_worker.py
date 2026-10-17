"""Background learning worker lifecycle tests."""
import threading
import unittest
from jarvis.learning_worker import learning_worker


class FakeLoop:
    def __init__(self, path):
        self.path = path

    def tick(self, *, enabled, max_pages):
        return {"status": "offline", "pages": 0}


class LearningWorkerTests(unittest.TestCase):
    def test_worker_stops_after_one_cycle(self):
        stop = threading.Event()
        results = []

        def on_result(result):
            results.append(result)
            stop.set()

        learning_worker(stop, "memory.db", interval_seconds=60,
                        loop_factory=FakeLoop, on_result=on_result)
        self.assertEqual(results, [{"status": "offline", "pages": 0}])

    def test_worker_respects_preexisting_stop(self):
        stop = threading.Event()
        stop.set()
        results = []
        learning_worker(stop, "memory.db", interval_seconds=60,
                        loop_factory=FakeLoop, on_result=results.append)
        self.assertEqual(results, [])

    def test_interval_validation(self):
        with self.assertRaises(ValueError):
            learning_worker(threading.Event(), "memory.db", interval_seconds=0,
                            loop_factory=FakeLoop)


if __name__ == "__main__":
    unittest.main()
