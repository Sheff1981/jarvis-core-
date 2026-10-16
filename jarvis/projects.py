"""Local project tracker for JARVIS. No network access or paid API."""
import sqlite3
import json
from pathlib import Path
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
        self.connection.execute("""CREATE TABLE IF NOT EXISTS project_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id),
            decision TEXT NOT NULL,
            rationale TEXT NOT NULL DEFAULT '',
            evidence TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )""")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS project_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id),
            idea TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued'
                CHECK(status IN ('queued','accepted','rejected')),
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

    def _require_project(self, project_id):
        if self.connection.execute("SELECT 1 FROM projects WHERE id=?",
                                   (project_id,)).fetchone() is None:
            raise KeyError("Project not found")

    @staticmethod
    def _required_text(value):
        if not isinstance(value, str) or not value.strip() or len(value) > 4096:
            raise ValueError("Expected nonempty text up to 4096 characters")
        return value.strip()

    def record_decision(self, project_id, decision, *, rationale="", evidence=""):
        decision = self._required_text(decision)
        if not all(isinstance(x, str) and len(x) <= 4096 for x in (rationale, evidence)):
            raise ValueError("Invalid decision metadata")
        with self.connection:
            self._require_project(project_id)
            cursor = self.connection.execute(
                """INSERT INTO project_decisions(project_id,decision,rationale,evidence,created_at)
                VALUES (?,?,?,?,?)""",
                (project_id,decision,rationale,evidence,datetime.now(timezone.utc).isoformat()))
        return cursor.lastrowid

    def decisions(self, project_id):
        self._require_project(project_id)
        return [dict(zip(("id","decision","rationale","evidence","created_at"), row))
                for row in self.connection.execute(
                    """SELECT id,decision,rationale,evidence,created_at FROM project_decisions
                    WHERE project_id=? ORDER BY id""", (project_id,))]

    def queue_idea(self, project_id, idea):
        idea = self._required_text(idea)
        with self.connection:
            self._require_project(project_id)
            cursor = self.connection.execute(
                "INSERT INTO project_ideas(project_id,idea,created_at) VALUES (?,?,?)",
                (project_id,idea,datetime.now(timezone.utc).isoformat()))
        return cursor.lastrowid

    def ideas(self, project_id):
        self._require_project(project_id)
        return [dict(zip(("id","idea","status"), row))
                for row in self.connection.execute(
                    "SELECT id,idea,status FROM project_ideas WHERE project_id=? ORDER BY id",
                    (project_id,))]

    def resolve_idea(self, project_id, idea_id, status):
        if status not in ("accepted", "rejected"):
            raise ValueError("Invalid idea disposition")
        with self.connection:
            self._require_project(project_id)
            cursor = self.connection.execute(
                """UPDATE project_ideas SET status=? WHERE id=? AND project_id=?
                AND status='queued'""", (status,idea_id,project_id))
            if cursor.rowcount != 1:
                raise ValueError("Idea not found or already resolved")

    def export_project(self, project_id):
        """Portable project JSON, excluding private journal and conversation turns."""
        self._require_project(project_id)
        row = self.connection.execute(
            "SELECT id,name,status,next_step,updated_at FROM projects WHERE id=?",
            (project_id,)).fetchone()
        checkpoints = self.connection.execute(
            """SELECT stage,task,status,last_action,evidence,blockers,next_step,created_at
            FROM project_checkpoints WHERE project_id=? ORDER BY id""",
            (project_id,)).fetchall()
        return json.dumps({
            "schema_version": 1,
            "project": dict(zip(("id","name","status","next_step","updated_at"),row)),
            "checkpoints": [dict(zip(("stage","task","status","last_action",
                "evidence","blockers","next_step","created_at"), item))
                for item in checkpoints],
            "decisions": self.decisions(project_id),
            "ideas": self.ideas(project_id),
        }, ensure_ascii=False, sort_keys=True)

    def delete_project(self, project_id, *, confirm=False):
        """Require explicit confirmation; preserve unrelated shared data."""
        if confirm is not True:
            raise PermissionError("Explicit confirmation required")
        with self.connection:
            self._require_project(project_id)
            self.connection.execute("DELETE FROM project_checkpoints WHERE project_id=?",
                                    (project_id,))
            self.connection.execute("DELETE FROM project_decisions WHERE project_id=?",
                                    (project_id,))
            self.connection.execute("DELETE FROM project_ideas WHERE project_id=?",
                                    (project_id,))
            self.connection.execute("DELETE FROM projects WHERE id=?", (project_id,))

    def backup(self, destination):
        """Consistent SQLite snapshot including all tables in the shared database."""
        target = Path(destination)
        source = self.connection.execute("PRAGMA database_list").fetchone()[2]
        if not source or target.resolve() == Path(source).resolve():
            raise ValueError("Backup destination must differ from source")
        if not target.parent.is_dir() or target.exists():
            raise ValueError("Backup destination must be a new file in an existing directory")
        with sqlite3.connect(str(target)) as backup_db:
            self.connection.backup(backup_db)
            result = backup_db.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise sqlite3.DatabaseError("Backup integrity check failed")
        return str(target)

    def close(self):
        self.connection.close()
