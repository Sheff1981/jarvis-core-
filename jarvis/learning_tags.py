"""Collect bounded Python release tag metadata; no claim of release-note verification."""
import argparse
import json
import re
import sqlite3
import urllib.request
from urllib.parse import quote
from jarvis.learning import LearningJournal

TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(?:[a-zA-Z0-9.]*)?$")
BASE = "https://api.github.com/repos/python/cpython/"
HEADERS = {"User-Agent": "JARVIS-Learning/0.1", "Accept": "application/vnd.github+json"}

def request_json(url, fetch=None):
    if fetch is not None:
        return fetch(url)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12) as response:
        if response.geturl() != url:
            raise ValueError("Unexpected API redirect")
        raw = response.read(32769)
    if len(raw) > 32768:
        raise ValueError("Oversized API response")
    return json.loads(raw)

def tag_metadata(tag, fetch=None):
    if not TAG.fullmatch(tag):
        raise ValueError("Invalid tag")
    ref = request_json(BASE + "git/ref/tags/" + quote(tag, safe=""), fetch)
    obj = ref.get("object", {})
    if ref.get("ref") != "refs/tags/" + tag or obj.get("type") not in ("tag", "commit"):
        raise ValueError("Unexpected tag reference")
    sha = obj.get("sha", "")
    if not re.fullmatch(r"[a-fA-F0-9]{40}", sha):
        raise ValueError("Invalid SHA")
    tag_sha = sha
    if obj["type"] == "tag":
        detail = request_json(BASE + "git/tags/" + sha, fetch)
        if detail.get("tag") != tag:
            raise ValueError("Mismatched annotated tag")
        obj = detail.get("object", {})
        sha = obj.get("sha", "")
        if obj.get("type") != "commit" or not re.fullmatch(r"[a-fA-F0-9]{40}", sha):
            raise ValueError("Invalid target commit")
    return {"tag": tag, "tag_sha": tag_sha, "commit_sha": sha,
            "source_url": "https://github.com/python/cpython/releases/tag/" + tag,
            "scope": "tag_metadata_only"}

def collect(db_path, fetch=None, limit=5):
    journal = LearningJournal(db_path)
    with sqlite3.connect(db_path) as db:
        rows = db.execute("""SELECT id,title FROM learning_events
            WHERE kind='rss' AND title LIKE 'v%' ORDER BY id DESC LIMIT ?""",
            (max(0, min(limit, 20)),)).fetchall()
    saved, failures = 0, []
    for source_id, tag in rows:
        if not TAG.fullmatch(tag):
            continue
        try:
            metadata = tag_metadata(tag, fetch)
            with sqlite3.connect(db_path) as db:
                exists = db.execute("""SELECT 1 FROM learning_events WHERE kind='release_tag'
                    AND json_extract(evidence,'$.source_event_id')=?""", (source_id,)).fetchone()
            if not exists:
                metadata["source_event_id"] = source_id
                journal.record("release_tag", tag, "collected", metadata)
                saved += 1
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            failures.append({"tag": tag, "reason": type(exc).__name__, "detail": str(exc)[:120]})
    return {"tags_collected": saved, "failures": failures}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="/var/lib/jarvis/learning.db")
    args = p.parse_args()
    print(json.dumps(collect(args.db)))

if __name__ == "__main__":
    main()
