"""Read-only retrieval from JARVIS collected documentation, with source attribution."""
import argparse
import json
import sqlite3

def search(db_path, query, limit=5):
    words = [word.casefold() for word in query.split() if len(word) >= 3][:8]
    if not words:
        return []
    limit = max(1, min(int(limit), 20))
    with sqlite3.connect(db_path) as db:
        rows = db.execute("""SELECT id,title,evidence,recorded_at
            FROM learning_events WHERE kind='official_doc' AND status='collected'
            ORDER BY id DESC LIMIT 500""").fetchall()
    matches = []
    seen_urls = set()
    for event_id, title, raw, recorded_at in rows:
        try:
            evidence = json.loads(raw)
            excerpt, url = evidence["excerpt"], evidence["url"]
            if evidence.get("scope") != "unreviewed_document_excerpt":
                continue
            if not isinstance(excerpt, str) or not isinstance(url, str):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            haystack = (title + " " + excerpt).casefold()
            score = sum(haystack.count(word) for word in words)
            if score:
                matches.append({"id": event_id, "title": title, "excerpt": excerpt,
                                "source_url": url, "recorded_at": recorded_at,
                                "status": "collected", "score": score})
        except (ValueError, TypeError, KeyError):
            continue
    matches.sort(key=lambda item: (-item["score"], -item["id"]))
    return matches[:limit]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("query")
    p.add_argument("--db", default="/var/lib/jarvis/learning.db")
    p.add_argument("--limit", type=int, default=5)
    args = p.parse_args()
    print(json.dumps({"query": args.query, "results": search(args.db, args.query, args.limit)},
                     ensure_ascii=False))

if __name__ == "__main__":
    main()
