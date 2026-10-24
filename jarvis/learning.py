"""Persistent, auditable learning event journal. Standard library only."""
import json
import sqlite3
from contextlib import contextmanager, closing
from datetime import datetime, timezone


class LearningJournal:
    def __init__(self, path="learning.db"):
        self.path = str(path)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS learning_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence TEXT NOT NULL
            )""")

    @contextmanager
    def _connect(self):
        with closing(sqlite3.connect(self.path, timeout=10)) as db, db:
            yield db

    def record(self, kind, title, status, evidence=None):
        if status not in {"collected", "verified", "failed"}:
            raise ValueError("Invalid learning status")
        if not kind.strip() or not title.strip():
            raise ValueError("kind and title must not be empty")
        evidence = evidence or {}
        if status == "verified" and not evidence:
            raise ValueError("Verified events require evidence")
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            cur = db.execute(
                "INSERT INTO learning_events(recorded_at,kind,title,status,evidence) VALUES (?,?,?,?,?)",
                (timestamp, kind, title, status, json.dumps(evidence, ensure_ascii=False)),
            )
            return cur.lastrowid

    def daily_report(self, day=None):
        day = day or datetime.now(timezone.utc).date().isoformat()
        with self._connect() as db:
            rows = db.execute(
                """SELECT kind,title,status,evidence,recorded_at FROM learning_events
                   WHERE substr(recorded_at,1,10)=? ORDER BY id""", (day,)
            ).fetchall()
        events = [
            {"kind": r[0], "title": r[1], "status": r[2],
             "evidence": json.loads(r[3]), "recorded_at": r[4]}
            for r in rows
        ]
        return {"date_utc": day, "total": len(events),
                "verified": sum(e["status"] == "verified" for e in events),
                "events": events}
