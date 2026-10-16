"""Isolated, consent-based session journal; never a training corpus."""
import sqlite3
from contextlib import closing


class PrivateSessionJournal:
    def __init__(self, path):
        self.path = str(path)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS private_session_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL
            )""")

    def append(self, session_id, role, content, *, consent=False):
        if consent is not True:
            raise PermissionError("Explicit consent required")
        if not isinstance(session_id, str) or not 1 <= len(session_id) <= 48:
            raise ValueError("Invalid session")
        if role not in ("user", "assistant"):
            raise ValueError("Invalid role")
        if not isinstance(content, str) or not 1 <= len(content.strip()) <= 2000:
            raise ValueError("Invalid content")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("INSERT INTO private_session_turns(session_id,role,content) VALUES (?,?,?)",
                       (session_id, role, content.strip()))

    def recent(self, session_id, *, limit=8):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Invalid limit")
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute("""SELECT role,content FROM
                (SELECT id,role,content FROM private_session_turns
                 WHERE session_id=? ORDER BY id DESC LIMIT ?) ORDER BY id""",
                (session_id, limit)).fetchall()
        return [{"role": role, "content": content} for role, content in rows]

    def forget(self, session_id):
        with closing(sqlite3.connect(self.path)) as db, db:
            return db.execute("DELETE FROM private_session_turns WHERE session_id=?",
                              (session_id,)).rowcount
