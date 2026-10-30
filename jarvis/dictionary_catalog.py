"""Local, source-attributed dictionary catalog for JARVIS.

The catalog stores references and licensing metadata, not copyrighted text.
No automatic downloading or training occurs.
"""
import json
import sqlite3
from contextlib import closing

CATEGORIES = frozenset({
    "explanatory", "orthographic", "orthoepic", "etymological",
    "phraseological", "morphological", "historical", "dialect",
    "terminological", "synonyms", "antonyms", "foreign_words",
    "stress", "pronunciation", "proverbs",
})
LICENSES = frozenset({"public_domain", "open_license", "permission", "unknown"})


class DictionaryCatalog:
    def __init__(self, path):
        self.path = str(path)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS dictionary_sources (
                source_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                provenance TEXT NOT NULL,
                license_status TEXT NOT NULL,
                license_evidence TEXT NOT NULL,
                modern_norm INTEGER NOT NULL CHECK(modern_norm IN (0,1)),
                import_allowed INTEGER NOT NULL CHECK(import_allowed IN (0,1)),
                CHECK(import_allowed=0 OR license_status IN
                      ('public_domain','open_license','permission'))
            )""")

    def register(self, *, source_id, title, category, provenance,
                 license_status="unknown", license_evidence="",
                 modern_norm=False):
        if not all(isinstance(x, str) and 0 < len(x.strip()) <= 500
                   for x in (source_id, title, provenance)):
            raise ValueError("Missing source metadata")
        if category not in CATEGORIES or license_status not in LICENSES:
            raise ValueError("Unsupported dictionary category or license")
        if not isinstance(license_evidence, str) or len(license_evidence) > 2000:
            raise ValueError("Invalid license evidence")
        if type(modern_norm) is not bool:
            raise TypeError("modern_norm must be boolean")
        allowed = license_status != "unknown" and bool(license_evidence.strip())
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""INSERT INTO dictionary_sources
                (source_id,title,category,provenance,license_status,
                 license_evidence,modern_norm,import_allowed)
                VALUES (?,?,?,?,?,?,?,?)""",
                (source_id.strip(), title.strip(), category, provenance.strip(),
                 license_status, license_evidence.strip(), int(modern_norm),
                 int(allowed)))
        return allowed

    def list_sources(self, *, importable_only=False):
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute("""SELECT source_id,title,category,license_status,
                modern_norm,import_allowed FROM dictionary_sources
                WHERE (?=0 OR import_allowed=1) ORDER BY source_id""",
                (int(bool(importable_only)),)).fetchall()
        return [dict(zip(("source_id", "title", "category", "license_status",
                          "modern_norm", "import_allowed"), row)) for row in rows]

    def export_manifest(self):
        return json.dumps(self.list_sources(), ensure_ascii=False, indent=2)
