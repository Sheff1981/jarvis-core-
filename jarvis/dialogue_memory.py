"""Persistent, local dialogue history. No network services required."""
import sqlite3
from datetime import datetime, timezone


class DialogueMemory:
    def __init__(self, db_path="jarvis.db"):
        self.connection = sqlite3.connect(db_path)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS dialogue_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_dialogue_project_id
            ON dialogue_messages(project_id, id)
        """)
        self.connection.commit()

    def append(self, project_id, role, content):
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required")
        if role not in ("user", "assistant"):
            raise ValueError("Unsupported dialogue role")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Message content is required")
        cursor = self.connection.execute(
            "INSERT INTO dialogue_messages(project_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (project_id.strip(), role, content.strip(), datetime.now(timezone.utc).isoformat()),
        )
        self.connection.commit()
        return cursor.lastrowid

    def recent(self, project_id, limit=20):
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id is required")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        rows = self.connection.execute(
            """SELECT id, role, content, created_at FROM dialogue_messages
               WHERE project_id=? ORDER BY id DESC LIMIT ?""",
            (project_id.strip(), limit),
        ).fetchall()
        return [dict(zip(("id", "role", "content", "created_at"), row)) for row in reversed(rows)]

    def close(self):
        self.connection.close()
