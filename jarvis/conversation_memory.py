"""Compatibility facade for the existing conversation_turns schema.

The canonical table is owned by ConversationStore (created REAL).
Do not create a competing schema in the same SQLite database.
"""
import time

from jarvis.conversation_store import ConversationStore


class ConversationMemory:
    def __init__(self, db_path="jarvis.db"):
        self.store = ConversationStore(db_path)

    def append(self, role, content):
        if role not in ("user", "assistant") or not isinstance(content, str):
            raise ValueError("Invalid conversation turn")
        with self.store.db:
            self.store.db.execute(
                "INSERT INTO conversation_turns(role,content,created) VALUES (?,?,?)",
                (role, content[:8000], time.time()),
            )

    def recent(self, limit=20):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Invalid history limit")
        rows = self.store.db.execute(
            "SELECT role,content FROM conversation_turns ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"role": role, "content": content} for role, content in reversed(rows)]

    def clear(self):
        self.store.clear()

    def close(self):
        self.store.close()
