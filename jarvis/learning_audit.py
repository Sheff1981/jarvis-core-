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
        if outcome not in ("pending_review", "error", "no_approved_source"):
            raise ValueError("Invalid outcome")
        self.db.execute(
            "INSERT INTO learning_research_attempts(goal_id,source_url,outcome,created_at) VALUES(?,?,?,?)",
            (goal_id, source_url, outcome, datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def recent(self, limit=20):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Invalid limit")
        rows = self.db.execute(
            "SELECT goal_id,source_url,outcome,created_at FROM learning_research_attempts ORDER BY id DESC LIMIT ?",
            (limit,))
        return [dict(zip(("goal_id", "source_url", "outcome", "created_at"), row)) for row in rows]

    def close(self):
        self.db.close()
