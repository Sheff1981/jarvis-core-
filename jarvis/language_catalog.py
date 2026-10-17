"""Extensible JARVIS programming-language curriculum.

Catalog entries are discovery targets, not claims of proficiency. Competence
is measured only by separately verified exercises and projects.
"""
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit


SEED_LANGUAGES = {
    "Python": "https://docs.python.org/3/",
    "Java": "https://docs.oracle.com/en/java/",
    "C++": "https://isocpp.org/",
    "C": "https://www.open-std.org/jtc1/sc22/wg14/",
    "C#": "https://learn.microsoft.com/en-us/dotnet/csharp/",
    "JavaScript": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
    "TypeScript": "https://www.typescriptlang.org/docs/",
    "PHP": "https://www.php.net/manual/en/",
    "Go": "https://go.dev/doc/",
    "Rust": "https://doc.rust-lang.org/book/",
    "Kotlin": "https://kotlinlang.org/docs/home.html",
    "Swift": "https://docs.swift.org/swift-book/documentation/the-swift-programming-language/",
    "Dart": "https://dart.dev/guides",
    "Ruby": "https://www.ruby-lang.org/en/documentation/",
    "SQL": "https://www.postgresql.org/docs/",
    "PowerShell": "https://learn.microsoft.com/en-us/powershell/",
    "Bash": "https://www.gnu.org/software/bash/manual/",
    "Lua": "https://www.lua.org/manual/",
    "R": "https://cran.r-project.org/manuals.html",
    "Julia": "https://docs.julialang.org/",
    "Scala": "https://docs.scala-lang.org/",
    "Elixir": "https://elixir-lang.org/docs.html",
    "Haskell": "https://www.haskell.org/documentation/",
    "Perl": "https://perldoc.perl.org/",
    "Zig": "https://ziglang.org/documentation/",
    "OCaml": "https://ocaml.org/docs",
    "Clojure": "https://clojure.org/guides/getting_started",
    "Erlang": "https://www.erlang.org/doc/",
    "Fortran": "https://fortran-lang.org/learn/",
    "COBOL": "https://www.ibm.com/docs/en/cobol-zos",
    "Assembly": "https://www.nasm.us/docs.php",
    "Objective-C": "https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ProgrammingWithObjectiveC/",
    "Groovy": "https://groovy-lang.org/documentation.html",
    "F#": "https://learn.microsoft.com/en-us/dotnet/fsharp/",
    "Visual Basic": "https://learn.microsoft.com/en-us/dotnet/visual-basic/",
    "MATLAB": "https://www.mathworks.com/help/matlab/",
    "Solidity": "https://docs.soliditylang.org/",
    "GDScript": "https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/",
}


class LanguageCatalog:
    def __init__(self, db_path="jarvis.db"):
        self.db = sqlite3.connect(db_path, timeout=10)
        self.db.execute("""CREATE TABLE IF NOT EXISTS programming_languages (
            name TEXT PRIMARY KEY, documentation_url TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'discovered',
            verified_exercises INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            CHECK(status IN ('discovered','studying','practiced','verified')))""")
        self.db.commit()

    def seed(self):
        for name, url in SEED_LANGUAGES.items():
            self.add(name, url)

    def add(self, name, documentation_url):
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValueError("Invalid language name")
        if not isinstance(documentation_url, str):
            raise ValueError("Invalid documentation URL")
        parsed = urlsplit(documentation_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Documentation must be HTTPS")
        self.db.execute("""INSERT OR IGNORE INTO programming_languages
            (name,documentation_url,updated_at) VALUES(?,?,?)""",
            (name.strip(), documentation_url, datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def list(self):
        rows = self.db.execute("""SELECT name,documentation_url,status,verified_exercises
            FROM programming_languages ORDER BY name""")
        return [dict(zip(("name","documentation_url","status","verified_exercises"), row)) for row in rows]

    def record_verified_exercise(self, name):
        result = self.db.execute("""UPDATE programming_languages
            SET verified_exercises=verified_exercises+1,
            status='practiced', updated_at=? WHERE name=?""",
            (datetime.now(timezone.utc).isoformat(), name))
        self.db.commit()
        if result.rowcount != 1:
            raise ValueError("Unknown language")

    def close(self):
        self.db.close()
