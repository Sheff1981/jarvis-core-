"""Conservative source validation: confirms provenance, not factual truth."""
import argparse
import json
import sqlite3
from contextlib import closing
from urllib.parse import urlsplit

from jarvis.learning import LearningJournal

TRUSTED = {
    "github.com": ("/python/cpython/releases/",),
    "www.python.org": ("/downloads/release/", "/doc/"),
}

def validate_source(url):
    try:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
            return False
        return any(parsed.path.startswith(prefix) for prefix in TRUSTED.get(parsed.hostname or "", ()))
    except ValueError:
        return False

def audit(db_path):
    """Append provenance audit events; do not upgrade headline claims to verified."""
    journal = LearningJournal(db_path)
    accepted = rejected = 0
    with closing(sqlite3.connect(db_path)) as db, db:
        rows = db.execute("SELECT id,title,evidence FROM learning_events WHERE kind='rss' AND status='collected'").fetchall()
        checked = {json.loads(row[0]).get("source_event_id") for row in db.execute(
            "SELECT evidence FROM learning_events WHERE kind='source_audit'")}
    for event_id, title, evidence in rows:
        if event_id in checked:
            continue
        try:
            url = json.loads(evidence).get("url", "")
        except (ValueError, TypeError):
            url = ""
        valid = validate_source(url)
        journal.record("source_audit", title, "verified" if valid else "failed",
                       {"source_event_id": event_id, "url": url,
                        "scope": "source_provenance_only", "rule": "trusted_https_path_v1"})
        accepted += bool(valid)
        rejected += not valid
    return {"source_accepted": accepted, "source_rejected": rejected}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="/var/lib/jarvis/learning.db")
    args = parser.parse_args()
    print(json.dumps(audit(args.db)))

if __name__ == "__main__":
    main()
