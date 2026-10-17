"""Local persistent audit trail for authorized computer actions."""
import sqlite3
import threading
import time


class ActionAudit:
    def __init__(self, db_path="jarvis.db"):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS action_audit ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "timestamp REAL NOT NULL, operation TEXT NOT NULL, "
            "target TEXT NOT NULL, status TEXT NOT NULL, detail TEXT NOT NULL)"
        )
        self._db.commit()

    def record(self, operation, target, status, detail=""):
        with self._lock:
            self._db.execute(
                "INSERT INTO action_audit(timestamp, operation, target, status, detail) "
                "VALUES (?, ?, ?, ?, ?)",
                (time.time(), operation, target, status, detail),
            )
            self._db.commit()

    def recent(self, limit=20):
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be 1..100")
        with self._lock:
            rows = self._db.execute(
                "SELECT timestamp, operation, target, status, detail "
                "FROM action_audit ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            {"timestamp": row[0], "operation": row[1], "target": row[2],
             "status": row[3], "detail": row[4]} for row in rows
        ]

    def close(self):
        with self._lock:
            if self._db is not None:
                self._db.close()
                self._db = None
