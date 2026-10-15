"""Bounded official Python documentation collector; provenance is not factual review."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import sqlite3
import urllib.request

from jarvis.learning import LearningJournal

PAGES = (
    "https://docs.python.org/3/whatsnew/3.14.html",
    "https://docs.python.org/3/tutorial/index.html",
    "https://docs.python.org/3/library/sqlite3.html",
)
MAX_BYTES = 512 * 1024

class MainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.main_depth = None
        self.ignore_depth = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        self.depth += 1
        attributes = dict(attrs)
        if self.main_depth is None and (tag == "main" or
            (tag == "div" and attributes.get("role") == "main")):
            self.main_depth = self.depth
        if self.main_depth is not None and self.ignore_depth is None and tag in ("script", "style", "nav"):
            self.ignore_depth = self.depth
        if self.main_depth is not None and self.ignore_depth is None and tag in ("p", "h1", "h2", "h3", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.ignore_depth == self.depth:
            self.ignore_depth = None
        if self.main_depth == self.depth:
            self.main_depth = None
        self.depth = max(0, self.depth - 1)

    def handle_data(self, data):
        if self.main_depth is not None and self.ignore_depth is None:
            self.parts.append(data)

def extract(data):
    if len(data) > MAX_BYTES:
        raise ValueError("Document too large")
    parser = MainText()
    parser.feed(data.decode("utf-8", errors="replace"))
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    return next((line[:1500] for line in lines if len(line) >= 100), "")

def fetch_page(url):
    if url not in PAGES:
        raise ValueError("URL not allowlisted")
    req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Learning/0.1"})
    with urllib.request.urlopen(req, timeout=12) as response:
        if response.geturl() != url:
            raise ValueError("Unexpected redirect")
        return response.read(MAX_BYTES)

def collect(db_path, fetch=fetch_page):
    journal = LearningJournal(db_path)
    saved, failures = 0, []
    for url in PAGES:
        try:
            excerpt = extract(fetch(url))
            if not excerpt:
                failures.append({"url": url, "reason": "no_main_excerpt"})
                continue
            digest = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
            with sqlite3.connect(db_path) as db:
                found = any(json.loads(raw).get("sha256") == digest and
                            json.loads(raw).get("url") == url for (raw,) in db.execute(
                                "SELECT evidence FROM learning_events WHERE kind='official_doc'"))
            if not found:
                journal.record("official_doc", url.rsplit("/", 1)[-1], "collected",
                               {"url": url, "excerpt": excerpt, "sha256": digest,
                                "scope": "unreviewed_document_excerpt"})
                saved += 1
        except (OSError, ValueError, UnicodeError) as exc:
            failures.append({"url": url, "reason": type(exc).__name__, "detail": str(exc)[:120]})
    return {"documents_collected": saved, "failures": failures}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="/var/lib/jarvis/learning.db")
    args = p.parse_args()
    print(json.dumps(collect(args.db), ensure_ascii=False))

if __name__ == "__main__":
    main()
