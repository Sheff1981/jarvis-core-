"""Persistent audit of autonomous research attempts; no claim of proficiency."""
from datetime import datetime, timezone
import sqlite3


class LearningAudit:
    def __init__(self, db_path="jarvis.db"):
        self.db = sqlite3.connect(db_path, timeout=10)
        self.db.execute("""CREATE TABLE IF NOT EXISTS learning_research_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            source_url TEXT,
            outcome TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        self.db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_review_once
            ON learning_research_attempts(goal_id,source_url) WHERE outcome='reviewed'""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS learning_practice_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            passed INTEGER NOT NULL CHECK(passed IN (0,1)),
            evidence TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        self.db.commit()

    def record(self, goal_id, outcome, source_url=None):
        if not isinstance(goal_id, int) or goal_id < 1:
            raise ValueError("Invalid goal")
        if outcome not in ("pending_review", "error", "no_approved_source", "reviewed"):
            raise ValueError("Invalid outcome")
        self.db.execute(
            "INSERT INTO learning_research_attempts(goal_id,source_url,outcome,created_at) VALUES(?,?,?,?)",
            (goal_id, source_url, outcome, datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def confirm_review(self, goal_id, source_url):
        """Record a review only if Academy confirms the source is reviewed."""
        if not isinstance(goal_id, int) or goal_id < 1 or not source_url:
            raise ValueError("Invalid review reference")
        row = self.db.execute(
            "SELECT reviewed FROM academy_sources WHERE url=?", (source_url,)).fetchone()
        if row is None or row[0] != 1:
            raise ValueError("Source is not reviewed")
        exists = self.db.execute(
            "SELECT 1 FROM learning_research_attempts WHERE goal_id=? AND source_url=? AND outcome='pending_review'",
            (goal_id, source_url)).fetchone()
        if exists is None:
            raise ValueError("No matching research attempt")
        if self.db.execute(
            "SELECT 1 FROM learning_research_attempts WHERE goal_id=? AND source_url=? AND outcome='reviewed'",
            (goal_id, source_url)).fetchone():
            return False
        self.db.execute("BEGIN IMMEDIATE")
        try:
            goal = self.db.execute(
                "SELECT status FROM learning_goals WHERE id=?", (goal_id,)).fetchone()
            if goal is None or goal[0] == "paused":
                raise ValueError("Unknown or paused learning goal")
            self.db.execute(
                "INSERT INTO learning_research_attempts(goal_id,source_url,outcome,created_at) VALUES(?,?,?,?)",
                (goal_id, source_url, "reviewed", datetime.now(timezone.utc).isoformat()))
            updated = self.db.execute(
                "UPDATE learning_goals SET status='active', completed_sessions=completed_sessions+1, last_studied=? WHERE id=? AND status!='paused'",
                (datetime.now(timezone.utc).isoformat(), goal_id))
            if updated.rowcount != 1:
                raise ValueError("Goal could not be updated")
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return True

    def record_practice(self, goal_id, skill, passed, evidence):
        """Persist an externally verified exercise result, not a self-claim."""
        from jarvis.academy import SKILLS
        if not isinstance(goal_id, int) or goal_id < 1:
            raise ValueError("Invalid goal")
        if skill not in SKILLS or not isinstance(passed, bool):
            raise ValueError("Invalid practice result")
        if not isinstance(evidence, str) or not 1 <= len(evidence.strip()) <= 500:
            raise ValueError("Missing practice evidence")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            goal = self.db.execute(
                "SELECT status FROM learning_goals WHERE id=?", (goal_id,)).fetchone()
            if goal is None or goal[0] == "paused":
                raise ValueError("Unknown or paused learning goal")
            self.db.execute(
                "INSERT INTO learning_practice_results(goal_id,skill,passed,evidence,created_at) VALUES(?,?,?,?,?)",
                (goal_id, skill, int(passed), evidence.strip(), datetime.now(timezone.utc).isoformat()))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def verify_practice(self, goal_id, exercise, answer):
        """Award at most one credit per approved exercise after local verification."""
        from jarvis.practice_verifier import PracticeVerifier
        skill = "python" if exercise.startswith("python-") else "mathematics"
        result = PracticeVerifier.verify(exercise, answer)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            goal = self.db.execute(
                "SELECT status,domain FROM learning_goals WHERE id=?", (goal_id,)).fetchone()
            if goal is None or goal[0] == "paused":
                raise ValueError("Unknown or paused learning goal")
            if goal[1] != ("programming" if exercise.startswith("python-") else "mathematics"):
                raise ValueError("Exercise does not match learning domain")
            self.db.execute("""CREATE TABLE IF NOT EXISTS learning_verified_exercises (
                goal_id INTEGER NOT NULL, exercise TEXT NOT NULL,
                evidence_sha256 TEXT NOT NULL, verified_at TEXT NOT NULL,
                PRIMARY KEY(goal_id, exercise))""")
            credited = False
            if result["passed"]:
                cursor = self.db.execute(
                    "INSERT OR IGNORE INTO learning_verified_exercises(goal_id,exercise,evidence_sha256,verified_at) VALUES(?,?,?,?)",
                    (goal_id, exercise, result["evidence_sha256"], datetime.now(timezone.utc).isoformat()))
                credited = cursor.rowcount == 1
                if credited:
                    self.db.execute(
                        "UPDATE learning_goals SET status='active',completed_sessions=completed_sessions+1,last_studied=? WHERE id=?",
                        (datetime.now(timezone.utc).isoformat(), goal_id))
            self.db.execute(
                "INSERT INTO learning_practice_results(goal_id,skill,passed,evidence,created_at) VALUES(?,?,?,?,?)",
                (goal_id, skill, int(result["passed"]), result["evidence_sha256"], datetime.now(timezone.utc).isoformat()))
            self.db.commit()
            return {"passed": result["passed"], "credited": credited}
        except Exception:
            self.db.rollback()
            raise

    def recent(self, limit=20):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Invalid limit")
        rows = self.db.execute(
            "SELECT goal_id,source_url,outcome,created_at FROM learning_research_attempts ORDER BY id DESC LIMIT ?",
            (limit,))
        return [dict(zip(("goal_id", "source_url", "outcome", "created_at"), row)) for row in rows]

    def close(self):
        self.db.close()
