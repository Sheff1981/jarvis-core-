"""Tests for evidence-based growth without fabricated server needs."""
import json
import tempfile
import unittest
from pathlib import Path

from jarvis.growth_planner import GrowthPlanner


class GrowthPlannerTests(unittest.TestCase):
    def setUp(self):
        self.planner = GrowthPlanner()

    def test_no_metrics_does_not_recommend_purchase(self):
        report = self.planner.assess({}, {})
        self.assertEqual(report.stage, "local")
        self.assertEqual(report.server_recommendation, "insufficient_data")
        self.assertIn("voice_reliable", report.next_goals)

    def test_resource_pressure_produces_evidence_based_suggestion(self):
        metrics = {"ram_total_gb": 8, "ram_peak_gb": 7.3,
                   "training_duration_seconds": 600, "training_target_seconds": 120}
        report = self.planner.assess(metrics, {"voice_reliable": True,
            "memory_persistent": True, "feedback_verified": True,
            "dataset_ready": True, "model_evaluated": True})
        self.assertEqual(report.server_recommendation, "consider_server")
        self.assertEqual(report.evidence["ram_peak_gb"], 7.3)

    def test_good_performance_keeps_local_hardware(self):
        report = self.planner.assess({"ram_total_gb": 8, "ram_peak_gb": 3,
            "training_duration_seconds": 30, "training_target_seconds": 120}, {})
        self.assertEqual(report.server_recommendation, "local_sufficient")

    def test_report_can_be_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            self.planner.save_report(path, self.planner.assess({}, {}))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["stage"], "local")


if __name__ == "__main__":
    unittest.main()
