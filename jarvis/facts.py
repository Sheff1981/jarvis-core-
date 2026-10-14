"""Explicit project facts stored locally in SQLite."""
import sqlite3


class FactStore:
    def __init__(self, path='jarvis.db'):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS remembered_facts (id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL, fact TEXT NOT NULL)')
        self.db.commit()

    def remember(self, project, fact):
        if not project.strip() or not fact.strip():
            raise ValueError('Project and fact are required')
        with self.db:
            cursor = self.db.execute('INSERT INTO remembered_facts(project, fact) VALUES (?, ?)', (project.strip(), fact.strip()))
        return cursor.lastrowid

    def list(self, project):
        rows = self.db.execute('SELECT id, fact FROM remembered_facts WHERE project = ? ORDER BY id DESC', (project.strip(),)).fetchall()
        return [{'id': item[0], 'fact': item[1]} for item in rows]

    def forget(self, fact_id):
        with self.db:
            cursor = self.db.execute('DELETE FROM remembered_facts WHERE id = ?', (fact_id,))
        return cursor.rowcount > 0

    def close(self):
        self.db.close()
