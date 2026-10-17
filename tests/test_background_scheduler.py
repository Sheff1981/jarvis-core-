"""Tests for priority order, deadlines and resource admission."""
import time
import unittest

from jarvis.background_scheduler import BackgroundScheduler, Priority
from jarvis.resource_governor import ResourceGovernor


class SchedulerTests(unittest.TestCase):
    def test_priority_order(self):
        output = []
        scheduler = BackgroundScheduler(ResourceGovernor(100))
        scheduler.submit("low", lambda: output.append("low"), Priority.LOW)
        scheduler.submit("high", lambda: output.append("high"), Priority.HIGH)
        scheduler.run_next()
        scheduler.run_next()
        self.assertEqual(output, ["high", "low"])

    def test_bounded_queue(self):
        scheduler = BackgroundScheduler(ResourceGovernor(100), max_pending=1)
        self.assertTrue(scheduler.submit("one", lambda: None))
        self.assertFalse(scheduler.submit("two", lambda: None))

    def test_expired_job(self):
        scheduler = BackgroundScheduler(ResourceGovernor(100))
        scheduler.submit("expired", lambda: self.fail("ran expired job"),
                         deadline=time.monotonic() - 1)
        self.assertFalse(scheduler.run_next())
        self.assertEqual(scheduler.snapshot()["expired"], 1)

    def test_budget_deferral(self):
        governor = ResourceGovernor(10)
        scheduler = BackgroundScheduler(governor)
        scheduler.submit("large", lambda: None, memory_mb=20)
        self.assertFalse(scheduler.run_next())
        self.assertEqual(scheduler.snapshot()["pending"], 1)

    def test_release_on_exception(self):
        governor = ResourceGovernor(10)
        scheduler = BackgroundScheduler(governor)
        def fail():
            raise RuntimeError("expected")
        scheduler.submit("broken", fail)
        with self.assertRaises(RuntimeError):
            scheduler.run_next()
        self.assertEqual(governor.snapshot()["reserved_mb"], 0)
        self.assertEqual(scheduler.snapshot()["failed"], 1)


if __name__ == "__main__":
    unittest.main()
