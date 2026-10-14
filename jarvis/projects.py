"""Local project tracker for JARVIS. No network access or paid API."""
import sqlite3
import uuid
from datetime import datetime, timezone

class Projects:
    def __init__(self, db_path="jarvis.db"):
        self.connection = sqlite3.connect(db_path)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                next_step TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def add(self, name, next_step=""):
        name = name.strip()
        if not name:
            raise ValueError("Project name cannot be empty")
        project_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            "INSERT INTO projects (id, name, next_step, updated_at) VALUES (?, ?, ?, ?)",
            (project_id, name, next_step.strip(), now))
        self.connection.commit()
        return project_id

    def list(self, include_done=False):
        query = "SELECT id, name, status, next_step FROM projects"
        if not include_done:
            query += " WHERE status != 'done'"
        query += " ORDER BY updated_at DESC"
        return [dict(zip(("id", "name", "status", "next_step"), row))
                for row in self.connection.execute(query)]

    def update(self, project_id, *, next_step=None, status=None):
        if status is not None and status not in ("active", "paused", "done"):
            raise ValueError("Invalid status")
        if next_step is None and status is None:
            raise ValueError("Nothing to update")
        row = self.connection.execute(
            "SELECT next_step, status FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None:
            raise KeyError("Project not found")
        new_step = row[0] if next_step is None else next_step.strip()
        new_status = row[1] if status is None else status
        self.connection.execute(
            "UPDATE projects SET next_step=?, status=?, updated_at=? WHERE id=?",
            (new_step, new_status, datetime.now(timezone.utc).isoformat(), project_id))
        self.connection.commit()

    def close(self):
        self.connection.close()
