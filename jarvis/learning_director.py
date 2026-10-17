"""Autonomous learning curriculum: persistent goals, priorities and bounded sessions.

Scheduling is local and opt-in. Goals are not proof of proficiency. External
sources are untrusted and require the Academy review process.
"""
from datetime import datetime, timezone
import sqlite3


DOMAINS = (
    "programming", "natural_languages", "history", "philosophy",
    "psychology", "mathematics", "science", "engineering",
    "cybersecurity", "product_research", "communication",
)


class LearningDirector:
    def __init__(self, db_path="jarvis.db"):
        self.db = sqlite3.connect(db_path, timeout=10)
        self.db.execute("""CREATE TABLE IF NOT EXISTS learning_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL, topic TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 3,
            status TEXT NOT NULL DEFAULT 'queued',
            last_studied TEXT,
            completed_sessions INTEGER NOT NULL DEFAULT 0,
            CHECK(priority BETWEEN 1 AND 5),
            CHECK(status IN ('queued','active','paused')))""")
        self.db.commit()

    def add_goal(self, domain, topic, priority=3):
        if domain not in DOMAINS or not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 160:
            raise ValueError("Invalid learning goal")
        if not isinstance(priority, int) or not 1 <= priority <= 5:
            raise ValueError("Invalid priority")
        row = self.db.execute("""INSERT INTO learning_goals(domain,topic,priority)
            VALUES(?,?,?)""", (domain, topic.strip(), priority))
        self.db.commit()
        return row.lastrowid

    def next_goals(self, limit=3):
        if not 1 <= limit <= 10:
            raise ValueError("Invalid session budget")
        rows = self.db.execute("""SELECT id,domain,topic,priority,completed_sessions
            FROM learning_goals WHERE status IN ('queued','active')
            ORDER BY priority DESC, completed_sessions ASC, id ASC LIMIT ?""", (limit,))
        return [dict(zip(("id","domain","topic","priority","completed_sessions"), row)) for row in rows]

    def record_session(self, goal_id, *, sources_reviewed=0, exercises_passed=0):
        if (not isinstance(sources_reviewed, int) or sources_reviewed < 0
                or not isinstance(exercises_passed, int) or exercises_passed < 0):
            raise ValueError("Invalid session evidence")
        if sources_reviewed == 0 and exercises_passed == 0:
            raise ValueError("A session requires verified evidence")
        result = self.db.execute("""UPDATE learning_goals SET
            status='active', completed_sessions=completed_sessions+1,
            last_studied=? WHERE id=? AND status!='paused'""",
            (datetime.now(timezone.utc).isoformat(), goal_id))
        self.db.commit()
        if result.rowcount != 1:
            raise ValueError("Unknown or paused goal")

    def pause(self, goal_id):
        self.db.execute("UPDATE learning_goals SET status='paused' WHERE id=?", (goal_id,))
        self.db.commit()

    def close(self):
        self.db.close()
