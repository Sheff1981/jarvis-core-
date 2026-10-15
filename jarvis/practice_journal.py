"""Evidence-based coding practice for JARVIS Academy.

Records externally verified test outcomes. This module never executes arbitrary
downloaded code, shell commands or untrusted programs.
"""
from datetime import datetime, timezone
import hashlib
import sqlite3
import json


class PracticeJournal:
    def __init__(self, db_path="jarvis.db"):
        self.db = sqlite3.connect(db_path, timeout=10)
        self.db.execute("""CREATE TABLE IF NOT EXISTS academy_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT NOT NULL,
            title TEXT NOT NULL,
            specification TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'proposed',
            created_at TEXT NOT NULL,
            CHECK(status IN ('proposed','ready','passed','failed')))""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS academy_evidence (
            exercise_id INTEGER NOT NULL,
            source_sha256 TEXT NOT NULL,
            test_report TEXT NOT NULL,
            passed INTEGER NOT NULL,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY(exercise_id) REFERENCES academy_exercises(id))""")
        self.db.commit()

    def propose(self, language, title, specification):
        if not all(isinstance(x, str) and 1 <= len(x.strip()) <= 8000
                   for x in (language, title, specification)):
            raise ValueError("Exercise fields must be nonempty and bounded")
        result = self.db.execute("""INSERT INTO academy_exercises
            (language,title,specification,created_at) VALUES(?,?,?,?)""",
            (language.strip(), title.strip(), specification.strip(),
             datetime.now(timezone.utc).isoformat()))
        self.db.commit()
        return result.lastrowid

    def record_external_test(self, exercise_id, source, report, *, passed, trusted_runner=False):
        if not trusted_runner:
            raise PermissionError("Only an explicitly trusted test runner can record evidence")
        if not isinstance(passed, bool) or not isinstance(source, str) or not source:
            raise ValueError("Invalid test evidence")
        if not isinstance(report, dict) or not report.get("runner") or not report.get("test_count"):
            raise ValueError("Test report must identify runner and executed tests")
        row = self.db.execute("SELECT status FROM academy_exercises WHERE id=?", (exercise_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown exercise")
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        self.db.execute("""INSERT INTO academy_evidence
            (exercise_id,source_sha256,test_report,passed,recorded_at) VALUES(?,?,?,?,?)""",
            (exercise_id, digest, json.dumps(report, ensure_ascii=False), int(passed),
             datetime.now(timezone.utc).isoformat()))
        self.db.execute("UPDATE academy_exercises SET status=? WHERE id=?",
                        ("passed" if passed else "failed", exercise_id))
        self.db.commit()
        return digest

    def summary(self):
        rows = self.db.execute("""SELECT language,status,COUNT(*) FROM academy_exercises
            GROUP BY language,status ORDER BY language,status""")
        summary = {}
        for language, status, count in rows:
            summary.setdefault(language, {})[status] = count
        return summary

    def close(self):
        self.db.close()
