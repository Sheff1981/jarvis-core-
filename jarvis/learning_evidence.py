"""Store bounded evidence excerpts without confusing provenance with factual verification."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit

MAX_EXCERPT = 2000

def add_evidence(db_path, source_event_id, claim, excerpt, source_url):
    """Record a cited claim as pending review; never auto-verify it."""
    claim, excerpt = claim.strip(), excerpt.strip()
    url = urlsplit(source_url)
    if not claim or not excerpt or len(claim) > 500 or len(excerpt) > MAX_EXCERPT:
        raise ValueError("Claim or excerpt is empty or too long")
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError("HTTPS evidence URL required")
    with sqlite3.connect(db_path, timeout=10) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS learning_evidence (
            id INTEGER PRIMARY KEY,
            source_event_id INTEGER NOT NULL,
            claim TEXT NOT NULL,
            excerpt TEXT NOT NULL,
            source_url TEXT NOT NULL,
            excerpt_sha256 TEXT NOT NULL,
            review_status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            UNIQUE(source_event_id, claim, excerpt_sha256)
        )""")
        found = db.execute("SELECT 1 FROM learning_events WHERE id=? AND kind='rss'",
                           (source_event_id,)).fetchone()
        if not found:
            raise ValueError("Source event does not exist")
        digest = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
        db.execute("""INSERT OR IGNORE INTO learning_evidence
            (source_event_id,claim,excerpt,source_url,excerpt_sha256,created_at)
            VALUES (?,?,?,?,?,?)""",
            (source_event_id, claim, excerpt, source_url, digest,
             datetime.now(timezone.utc).isoformat()))
        return db.execute("""SELECT id FROM learning_evidence
            WHERE source_event_id=? AND claim=? AND excerpt_sha256=?""",
            (source_event_id, claim, digest)).fetchone()[0]

def pending_evidence(db_path):
    with sqlite3.connect(db_path, timeout=10) as db:
        return [dict(zip(("id","claim","excerpt","source_url","review_status"), row))
                for row in db.execute("""SELECT id,claim,excerpt,source_url,review_status
                    FROM learning_evidence WHERE review_status='pending' ORDER BY id""")]
