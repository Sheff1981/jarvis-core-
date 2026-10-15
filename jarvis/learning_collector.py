"""Conservative RSS intake: collect headlines as unverified observations."""
import argparse
import json
import sqlite3
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from jarvis.learning import LearningJournal

DEFAULT_FEED = "https://github.com/python/cpython/releases.atom"


def parse_feed(data):
    root = ET.fromstring(data)
    items = root.findall("./channel/item")
    if items:
        return [(item.findtext("title", "").strip(), item.findtext("link", "").strip())
                for item in items]
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("./atom:entry", ns)
    return [(entry.findtext("atom:title", "", ns).strip(),
             next((link.get("href", "").strip() for link in entry.findall("atom:link", ns)
                   if link.get("rel", "alternate") == "alternate"), ""))
            for entry in entries]


def collect(feed_url, db_path, fetch=None, limit=10):
    parts = urlsplit(feed_url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("Only public HTTPS feeds are supported")
    if fetch is None:
        def fetch(url):
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Learning/0.1"})
            with urllib.request.urlopen(req, timeout=12) as response:
                return response.read(1024 * 1024 + 1)
    data = fetch(feed_url)
    if len(data) > 1024 * 1024:
        raise ValueError("Feed exceeds 1 MiB")
    journal = LearningJournal(db_path)
    count = 0
    with sqlite3.connect(db_path) as db:
        known = {json.loads(row[0]).get("url") for row in
                 db.execute("SELECT evidence FROM learning_events WHERE kind='rss'")}
    for title, link in parse_feed(data)[:limit]:
        parsed = urlsplit(link)
        if not title or parsed.scheme != "https" or not parsed.hostname or link in known:
            continue
        journal.record("rss", title, "collected", {"url": link, "feed": feed_url})
        known.add(link)
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed", default=DEFAULT_FEED)
    parser.add_argument("--db", default="/var/lib/jarvis/learning.db")
    args = parser.parse_args()
    print(json.dumps({"collected": collect(args.feed, args.db)}))


if __name__ == "__main__":
    main()
