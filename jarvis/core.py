import json
import sqlite3
import time
import uuid

class Memory:
    def __init__(self, path='jarvis.db'):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS scenarios (id TEXT PRIMARY KEY, name TEXT NOT NULL, platform TEXT NOT NULL, steps TEXT NOT NULL, created REAL NOT NULL)')
        self.db.commit()

    def save(self, name, platform, steps):
        sid = str(uuid.uuid4())
        self.db.execute('INSERT INTO scenarios VALUES (?,?,?,?,?)', (sid, name, platform, json.dumps(steps, ensure_ascii=False), time.time()))
        self.db.commit()
        return sid

    def get(self, sid):
        row = self.db.execute('SELECT name, platform, steps FROM scenarios WHERE id=?', (sid,)).fetchone()
        if not row:
            raise KeyError('Scenario not found')
        return {'name': row[0], 'platform': row[1], 'steps': json.loads(row[2])}

    def list(self):
        return self.db.execute('SELECT id, name, platform FROM scenarios ORDER BY created DESC').fetchall()
