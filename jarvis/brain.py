"""Local JARVIS brain: durable facts, task planning and guarded execution policy."""
import sqlite3
from datetime import datetime, timezone


class Brain:
    """SQLite-backed knowledge and plans. Never executes system commands."""

    def __init__(self, db_path="jarvis.db"):
        self.db = sqlite3.connect(db_path, timeout=10)
        self.db.execute("""CREATE TABLE IF NOT EXISTS brain_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL, fact_key TEXT NOT NULL,
            fact_value TEXT NOT NULL, updated_at TEXT NOT NULL,
            UNIQUE(scope, fact_key))""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS brain_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL, title TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'proposed',
            created_at TEXT NOT NULL,
            CHECK(state IN ('proposed','approved','running','done','failed')))""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS brain_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL, situation TEXT NOT NULL,
            correction TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL)""")
        self.db.commit()

    def remember(self, scope, key, value):
        if not all(isinstance(x, str) and x.strip() for x in (scope, key, value)):
            raise ValueError("Memory fields must be nonempty strings")
        if max(map(len, (scope, key, value))) > 4096:
            raise ValueError("Memory entry too long")
        self.db.execute("""INSERT INTO brain_facts(scope,fact_key,fact_value,updated_at)
            VALUES(?,?,?,?) ON CONFLICT(scope,fact_key) DO UPDATE SET
            fact_value=excluded.fact_value,updated_at=excluded.updated_at""",
            (scope.strip(), key.strip(), value.strip(), datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def recall(self, scope, limit=20):
        if not isinstance(scope, str) or not scope.strip() or not 1 <= limit <= 100:
            raise ValueError("Invalid memory query")
        rows = self.db.execute("""SELECT fact_key,fact_value FROM brain_facts
            WHERE scope=? ORDER BY updated_at DESC LIMIT ?""", (scope, limit))
        return dict(rows)

    def propose(self, scope, title):
        if not isinstance(scope, str) or not scope.strip() or not isinstance(title, str) or not title.strip():
            raise ValueError("Task requires scope and title")
        cursor = self.db.execute("""INSERT INTO brain_tasks(scope,title,created_at)
            VALUES(?,?,?)""", (scope.strip(), title.strip(), datetime.now(timezone.utc).isoformat()))
        self.db.commit()
        return cursor.lastrowid

    def tasks(self, scope):
        return [dict(zip(("id", "title", "state"), row)) for row in self.db.execute(
            "SELECT id,title,state FROM brain_tasks WHERE scope=? ORDER BY id", (scope,))]

    def approve(self, task_id):
        result = self.db.execute(
            "UPDATE brain_tasks SET state='approved' WHERE id=? AND state='proposed'", (task_id,))
        self.db.commit()
        if result.rowcount != 1:
            raise ValueError("Task missing or not awaiting approval")

    def learn(self, scope, situation, correction):
        """Store feedback as a candidate lesson, not an unquestioned fact."""
        if not all(isinstance(x, str) and x.strip() for x in (scope, situation, correction)):
            raise ValueError("Learning requires scope, situation and correction")
        if any(len(x) > 4096 for x in (scope, situation, correction)):
            raise ValueError("Learning entry too long")
        cursor = self.db.execute("""INSERT INTO brain_feedback
            (scope,situation,correction,created_at) VALUES(?,?,?,?)""",
            (scope.strip(), situation.strip(), correction.strip(), datetime.now(timezone.utc).isoformat()))
        self.db.commit()
        return cursor.lastrowid

    def lessons(self, scope, verified_only=True, limit=20):
        if not isinstance(scope, str) or not scope.strip() or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Invalid lesson query")
        rows = self.db.execute("""SELECT id,situation,correction,verified FROM brain_feedback
            WHERE scope=? AND (?=0 OR verified=1) ORDER BY id DESC LIMIT ?""",
            (scope, int(verified_only), limit))
        return [dict(zip(("id","situation","correction","verified"), row)) for row in rows]

    def verify_lesson(self, lesson_id):
        result = self.db.execute("UPDATE brain_feedback SET verified=1 WHERE id=?", (lesson_id,))
        self.db.commit()
        if result.rowcount != 1:
            raise ValueError("Unknown lesson")

    def close(self):
        self.db.close()
