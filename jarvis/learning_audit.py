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
        self.record(goal_id, "reviewed", source_url)
        return True

    def recent(self, limit=20):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Invalid limit")
        rows = self.db.execute(
            "SELECT goal_id,source_url,outcome,created_at FROM learning_research_attempts ORDER BY id DESC LIMIT ?",
            (limit,))
        return [dict(zip(("goal_id", "source_url", "outcome", "created_at"), row)) for row in rows]

    def close(self):
        self.db.close()
