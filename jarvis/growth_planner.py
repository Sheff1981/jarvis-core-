"""JARVIS growth roadmap and evidence-based hardware recommendations.

Planning is autonomous; spending, migration and code deployment remain
owner-authorized. The planner does not invent performance measurements.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


STAGES = (
    ("local", "Local assistant", "Reliable offline speech, dialogue and persistent memory"),
    ("learning", "Experience learner", "Verified lessons, feedback and reusable skills"),
    ("models", "Model builder", "Labeled datasets, CPU training, holdout evaluation"),
    ("distributed", "Distributed assistant", "Owner-approved migration to remote compute"),
)


@dataclass(frozen=True)
class GrowthAssessment:
    stage: str
    blockers: tuple
    next_goals: tuple
    server_recommendation: str
    evidence: dict

    def as_dict(self):
        return {"stage": self.stage, "blockers": list(self.blockers),
                "next_goals": list(self.next_goals),
                "server_recommendation": self.server_recommendation,
                "evidence": self.evidence}


class GrowthPlanner:
    def assess(self, metrics, capabilities):
        if not isinstance(metrics, dict) or not isinstance(capabilities, dict):
            raise ValueError("Metrics and capabilities must be mappings")
        capabilities = {key: value is True for key, value in capabilities.items()}
        required = ("voice_reliable", "memory_persistent", "feedback_verified",
                    "dataset_ready", "model_evaluated", "remote_migration_tested")
        missing = tuple(name for name in required if not capabilities.get(name, False))
        if missing[:2]:
            stage = "local"
        elif missing[2:3]:
            stage = "learning"
        elif missing[3:5]:
            stage = "models"
        else:
            stage = "distributed" if not missing else "models"
        goals = missing[:3]
        evidence = {}
        for name in ("ram_total_gb", "ram_peak_gb", "cpu_peak_pct",
                     "training_duration_seconds", "training_target_seconds"):
            value = metrics.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                evidence[name] = value
        recommendation = "insufficient_data"
        if all(name in evidence for name in ("ram_total_gb", "ram_peak_gb",
                                             "training_duration_seconds", "training_target_seconds")):
            memory_pressure = (evidence["ram_total_gb"] > 0 and
                               evidence["ram_peak_gb"] / evidence["ram_total_gb"] >= 0.85)
            training_slow = (evidence["training_target_seconds"] > 0 and
                             evidence["training_duration_seconds"] >
                             2 * evidence["training_target_seconds"])
            recommendation = "consider_server" if memory_pressure or training_slow else "local_sufficient"
        return GrowthAssessment(stage, missing, goals, recommendation, evidence)

    def save_report(self, path, assessment):
        path = Path(path)
        if path.suffix.lower() != ".json":
            raise ValueError("Growth report must be JSON")
        report = assessment.as_dict()
        report["created_at"] = datetime.now(timezone.utc).isoformat()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report
