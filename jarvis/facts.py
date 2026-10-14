"""Explicit project facts stored locally in SQLite."""
import sqlite3


class FactStore:
    def __init__(self, path="jarvis.db"):
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS remembered_facts "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL, fact TEXT NOT NULL)"
        )
        self.db.commit()

    def remember(self, project, fact):
        project, fact = project.strip(), fact.strip()
        if not project or not fact:
            raise ValueError("Project and fact are required")
        # Existing databases are supported without schema migration.
        rows = self.db.execute(
            "SELECT id, project, fact FROM remembered_facts ORDER BY id"
        ).fetchall()
        for fact_id, saved_project, saved_fact in rows:
            if saved_project.casefold() == project.casefold() and saved_fact.casefold() == fact.casefold():
                return fact_id
        with self.db:
            cursor = self.db.execute(
                "INSERT INTO remembered_facts(project, fact) VALUES (?, ?)",
                (project, fact),
            )
        return cursor.lastrowid

    def list(self, project):
        project = project.strip().casefold()
        rows = self.db.execute(
            "SELECT id, project, fact FROM remembered_facts ORDER BY id DESC"
        ).fetchall()
        return [
            {"id": fact_id, "fact": fact}
            for fact_id, saved_project, fact in rows
            if saved_project.casefold() == project
        ]

    def forget(self, fact_id):
        with self.db:
            cursor = self.db.execute(
                "DELETE FROM remembered_facts WHERE id = ?", (fact_id,)
            )
        return cursor.rowcount > 0

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
