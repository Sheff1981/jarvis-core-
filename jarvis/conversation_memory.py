"""Durable conversation turns, kept separate from project records."""
import sqlite3
from datetime import datetime, timezone


class ConversationMemory:
    def __init__(self, db_path="jarvis.db"):
        self.connection = sqlite3.connect(db_path)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS conversation_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def append(self, role, content):
        if role not in ("user", "assistant") or not isinstance(content, str):
            raise ValueError("Invalid conversation turn")
        self.connection.execute(
            "INSERT INTO conversation_turns (role,content,created_at) VALUES (?,?,?)",
            (role, content[:8000], datetime.now(timezone.utc).isoformat()))
        self.connection.commit()

    def recent(self, limit=20):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Invalid history limit")
        rows = self.connection.execute(
            "SELECT role,content FROM conversation_turns ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()
        return list(reversed([{"role": role, "content": content} for role, content in rows]))

    def clear(self):
        self.connection.execute("DELETE FROM conversation_turns")
        self.connection.commit()

    def close(self):
        self.connection.close()
