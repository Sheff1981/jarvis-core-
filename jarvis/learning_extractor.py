"""Bounded extraction from explicitly allowlisted Python release pages."""
import argparse
from html.parser import HTMLParser
import json
import sqlite3
import urllib.request
from urllib.parse import urlsplit

from jarvis.learning_evidence import add_evidence
from jarvis.learning_verifier import validate_source

MAX_HTML = 512 * 1024

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = 0
        self.release_depth = 0
        self.depth = 0
        self.found_release = False
    def handle_starttag(self, tag, attrs):
        self.depth += 1
        attributes = dict(attrs)
        if attributes.get("data-test-selector") == "body-content" or "markdown-body" in attributes.get("class", "").split():
            self.release_depth = self.depth
            self.found_release = True
        if tag in ("script", "style", "nav", "footer", "header"):
            self.ignored += 1
        if self.release_depth and tag in ("p", "li", "h1", "h2", "h3"):
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header") and self.ignored:
            self.ignored -= 1
        if self.release_depth == self.depth:
            self.release_depth = 0
        self.depth = max(0, self.depth - 1)
    def handle_data(self, data):
        if self.release_depth and not self.ignored:
            self.parts.append(data)

def extract_excerpt(data):
    if len(data) > MAX_HTML:
        raise ValueError("HTML too large")
    parser = TextExtractor()
    parser.feed(data.decode("utf-8", errors="replace"))
    if not parser.found_release:
        return ""
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    blocks = [line for line in lines if line and len(line) >= 12]
    for index, line in enumerate(blocks):
        if len(line) >= 80:
            return line[:1500]
        combined = " ".join(blocks[index:index + 8])[:1500]
        if len(combined) >= 80:
            return combined
    return ""

def collect_evidence(db_path, fetch=None, limit=5):
    """Capture source text as a pending excerpt, not an inferred factual claim."""
    if fetch is None:
        def fetch(url):
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Learning/0.1"})
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
            with opener.open(req, timeout=12) as response:
                if not validate_source(response.geturl()):
                    raise ValueError("Redirect outside trusted source")
                return response.read(MAX_HTML + 1)
    with sqlite3.connect(db_path) as db:
        rows = db.execute("""SELECT e.id,e.title,e.evidence FROM learning_events e
            JOIN learning_events a ON json_extract(a.evidence,'$.source_event_id')=e.id
            WHERE e.kind='rss' AND a.kind='source_audit' AND a.status='verified'
            ORDER BY e.id DESC LIMIT ?""", (limit,)).fetchall()
    saved = 0
    failures = []
    for event_id, title, raw in rows:
        url = json.loads(raw).get("url", "")
        if not validate_source(url):
            continue
        try:
            excerpt = extract_excerpt(fetch(url))
            if excerpt:
                add_evidence(db_path, event_id, title, excerpt, url)
                saved += 1
            else:
                failures.append({"event_id": event_id, "reason": "no_suitable_excerpt"})
        except (OSError, ValueError, UnicodeError) as exc:
            failures.append({"event_id": event_id, "reason": type(exc).__name__, "detail": str(exc)[:160]})
    return {"evidence_candidates": saved, "failures": failures}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="/var/lib/jarvis/learning.db")
    args = p.parse_args()
    print(json.dumps(collect_evidence(args.db)))

if __name__ == "__main__":
    main()
