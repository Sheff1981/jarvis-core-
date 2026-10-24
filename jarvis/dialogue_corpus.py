"""Curated, consent-based dialogue examples for future offline fine-tuning.

This stores training examples only; it never changes model weights.
"""
import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


class DialogueCorpus:
    def __init__(self, path):
        self.path = str(path)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS dialogue_corpus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                digest TEXT NOT NULL UNIQUE,
                user_text TEXT NOT NULL,
                assistant_text TEXT NOT NULL,
                source TEXT NOT NULL,
                consent INTEGER NOT NULL CHECK(consent=1),
                reviewed INTEGER NOT NULL DEFAULT 0 CHECK(reviewed IN (0,1)),
                created_at TEXT NOT NULL
            )""")

    def submit(self, user_text, assistant_text, *, source, consent=False):
        if consent is not True:
            raise PermissionError("Explicit consent is required")
        if source not in ("owner", "curated"):
            raise ValueError("Unapproved dialogue source")
        for value in (user_text, assistant_text):
            if not isinstance(value, str) or not 1 <= len(value.strip()) <= 2000:
                raise ValueError("Invalid dialogue length")
        user_text, assistant_text = user_text.strip(), assistant_text.strip()
        digest = hashlib.sha256(json.dumps(
            [user_text, assistant_text], ensure_ascii=False).encode("utf-8")).hexdigest()
        with closing(sqlite3.connect(self.path)) as db, db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO dialogue_corpus(digest,user_text,assistant_text,source,consent,created_at) VALUES(?,?,?,?,1,?)",
                (digest, user_text, assistant_text, source, datetime.now(timezone.utc).isoformat()))
            return cursor.rowcount == 1

    def review(self, digest, *, approved=False):
        if approved is not True:
            raise PermissionError("Explicit approval is required")
        with closing(sqlite3.connect(self.path)) as db, db:
            cursor = db.execute(
                "UPDATE dialogue_corpus SET reviewed=1 WHERE digest=? AND consent=1 AND reviewed=0",
                (digest,))
            return cursor.rowcount == 1

    def pending(self, limit=20):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Invalid limit")
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute(
                "SELECT digest,user_text,assistant_text,source FROM dialogue_corpus WHERE reviewed=0 ORDER BY id LIMIT ?",
                (limit,)).fetchall()
        return [dict(zip(("digest", "user", "assistant", "source"), row)) for row in rows]

    def export_approved(self):
        """Return only reviewed examples in chat fine-tuning message format."""
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute(
                "SELECT user_text,assistant_text FROM dialogue_corpus WHERE consent=1 AND reviewed=1 ORDER BY id"
            ).fetchall()
        return [{"messages": [{"role": "user", "content": user},
                              {"role": "assistant", "content": assistant}]}
                for user, assistant in rows]
