"""Import locally supplied licensed dictionary JSONL into an attributed SQLite index.

Never fetches remote content, modifies model weights, or treats historical
dictionary entries as contemporary normative spellings.
"""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from jarvis.dictionary_catalog import DictionaryCatalog


class DictionaryIndex:
    def __init__(self, path):
        self.path = str(path)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS dictionary_entries (
                source_id TEXT NOT NULL,
                lemma TEXT NOT NULL,
                definition TEXT NOT NULL,
                category TEXT NOT NULL,
                modern_norm INTEGER NOT NULL CHECK(modern_norm IN (0,1)),
                PRIMARY KEY (source_id,lemma,definition)
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_dictionary_lemma ON dictionary_entries(lemma)")

    def import_jsonl(self, catalog, source_id, input_path, *, max_entries=100000):
        if not isinstance(catalog, DictionaryCatalog):
            raise TypeError("Expected dictionary catalog")
        matches = [row for row in catalog.list_sources(importable_only=True)
                   if row["source_id"] == source_id]
        if not matches:
            raise PermissionError("Source has no recorded import authorization")
        source = matches[0]
        if type(max_entries) is not int or not 1 <= max_entries <= 1000000:
            raise ValueError("Invalid import limit")
        input_path = Path(input_path)
        if input_path.stat().st_size > 100 * 1024 * 1024:
            raise ValueError("Input file too large")
        count = 0
        with input_path.open(encoding="utf-8") as stream, closing(sqlite3.connect(self.path)) as db, db:
            for line in stream:
                if not line.strip():
                    continue
                count += 1
                if count > max_entries:
                    raise ValueError("Import limit exceeded")
                if len(line) > 8192:
                    raise ValueError("Entry too large")
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("Invalid dictionary entry")
                lemma, definition = record.get("lemma"), record.get("definition")
                if not isinstance(lemma, str) or not 1 <= len(lemma.strip()) <= 120:
                    raise ValueError("Invalid lemma")
                if not isinstance(definition, str) or not 1 <= len(definition.strip()) <= 4000:
                    raise ValueError("Invalid definition")
                db.execute("""INSERT OR IGNORE INTO dictionary_entries
                    (source_id,lemma,definition,category,modern_norm)
                    VALUES (?,?,?,?,?)""",
                    (source_id, lemma.strip().casefold(), definition.strip(),
                     source["category"], source["modern_norm"]))
        return count

    def lookup(self, lemma, *, limit=10):
        if not isinstance(lemma, str) or not 1 <= len(lemma.strip()) <= 120:
            raise ValueError("Invalid lemma")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Invalid limit")
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute("""SELECT source_id,definition,category,modern_norm
                FROM dictionary_entries WHERE lemma=? ORDER BY modern_norm DESC,source_id
                LIMIT ?""", (lemma.strip().casefold(), limit)).fetchall()
        return [dict(zip(("source_id", "definition", "category", "modern_norm"), row))
                for row in rows]
