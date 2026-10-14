"""Persistent local conversation history; no network and no automatic uploads."""
import sqlite3
import time


class ConversationStore:
    def __init__(self, path="jarvis.db"):
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS conversation_turns "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, "
            "content TEXT NOT NULL, created REAL NOT NULL)"
        )
        self.db.commit()

    def append_exchange(self, prompt, answer):
        """Save both turns atomically, only after successful model response."""
        if not prompt.strip() or not answer.strip():
            raise ValueError("Both messages must be nonempty")
        with self.db:
            self.db.executemany(
                "INSERT INTO conversation_turns(role, content, created) VALUES (?,?,?)",
                (("user", prompt, time.time()), ("assistant", answer, time.time())),
            )

    def recent(self, max_turns=8):
        if not isinstance(max_turns, int) or max_turns < 1:
            raise ValueError("max_turns must be positive")
        rows = self.db.execute(
            "SELECT role, content FROM conversation_turns "
            "ORDER BY id DESC LIMIT ?", (max_turns * 2,)
        ).fetchall()
        return [{"role": role, "content": content} for role, content in reversed(rows)]

    def clear(self):
        with self.db:
            self.db.execute("DELETE FROM conversation_turns")

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
