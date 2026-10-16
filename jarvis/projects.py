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
        self.connection.execute("""CREATE TABLE IF NOT EXISTS project_checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id),
            stage TEXT NOT NULL,
            task TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('planned','running','blocked','done')),
            last_action TEXT NOT NULL DEFAULT '',
            evidence TEXT NOT NULL DEFAULT '',
            blockers TEXT NOT NULL DEFAULT '',
            next_step TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )""")
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

    def checkpoint(self, project_id, *, stage, task, status, last_action="",
                   evidence="", blockers="", next_step=""):
        """Append a durable checkpoint without modifying conversation or private data."""
        if status not in ("planned", "running", "blocked", "done"):
            raise ValueError("Invalid checkpoint status")
        fields = (stage, task, last_action, evidence, blockers, next_step)
        if any(not isinstance(value, str) or len(value) > 4096 for value in fields):
            raise ValueError("Invalid checkpoint field")
        if not stage.strip() or not task.strip():
            raise ValueError("Stage and task required")
        with self.connection:
            if self.connection.execute("SELECT 1 FROM projects WHERE id=?",
                                       (project_id,)).fetchone() is None:
                raise KeyError("Project not found")
            cursor = self.connection.execute(
                """INSERT INTO project_checkpoints
                (project_id,stage,task,status,last_action,evidence,blockers,next_step,created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (project_id,stage.strip(),task.strip(),status,last_action,evidence,
                 blockers,next_step,datetime.now(timezone.utc).isoformat()))
            self.connection.execute(
                "UPDATE projects SET next_step=?,updated_at=? WHERE id=?",
                (next_step,datetime.now(timezone.utc).isoformat(),project_id))
        return cursor.lastrowid

    def latest_checkpoint(self, project_id):
        row = self.connection.execute(
            """SELECT id,stage,task,status,last_action,evidence,blockers,next_step,created_at
            FROM project_checkpoints WHERE project_id=? ORDER BY id DESC LIMIT 1""",
            (project_id,)).fetchone()
        if row is None:
            return None
        keys = ("id","stage","task","status","last_action","evidence",
                "blockers","next_step","created_at")
        return dict(zip(keys,row))

    def close(self):
        self.connection.close()
