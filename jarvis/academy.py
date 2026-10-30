"""JARVIS Academy: curated documentation, verified notes and skill progression.

External pages are untrusted educational material, never instructions to execute.
The crawler is intentionally limited to an explicit source allowlist and bounded pages.
"""
from datetime import datetime, timezone
from html.parser import HTMLParser
import ipaddress
import json
import socket
import sqlite3
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen


SOURCES = {
    "python": ("docs.python.org",),
    "web": ("developer.mozilla.org", "html.spec.whatwg.org"),
    "wordpress": ("developer.wordpress.org",),
    "joomla": ("manual.joomla.org", "docs.joomla.org"),
    "opencart": ("docs.opencart.com", "opencart.com"),
    "php": ("www.php.net",),
    "security": ("cheatsheetseries.owasp.org",),
}
SKILLS = ("python", "web", "wordpress", "joomla", "opencart", "php", "security")


class _PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        return " ".join(" ".join(self.parts).split())


class Academy:
    def __init__(self, db_path="jarvis.db"):
        self.db = sqlite3.connect(db_path, timeout=10)
        self.db.execute("""CREATE TABLE IF NOT EXISTS academy_sources (
            url TEXT PRIMARY KEY, skill TEXT NOT NULL, title TEXT NOT NULL,
            excerpt TEXT NOT NULL, fetched_at TEXT NOT NULL,
            reviewed INTEGER NOT NULL DEFAULT 0)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS academy_progress (
            skill TEXT PRIMARY KEY, completed_exercises INTEGER NOT NULL DEFAULT 0,
            passed_exercises INTEGER NOT NULL DEFAULT 0)""")
        self.db.commit()

    @staticmethod
    def check_url(url, skill):
        if skill not in SOURCES:
            raise ValueError("Unknown skill")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError("Only public HTTPS documentation is permitted")
        if parsed.hostname not in SOURCES[skill]:
            raise ValueError("Documentation domain is not allowlisted")
        if parsed.fragment:
            raise ValueError("Fragment URLs are not allowed")
        return url

    def ingest(self, url, skill, *, opener=None, max_bytes=250000):
        self.check_url(url, skill)
        if not 1000 <= max_bytes <= 1000000:
            raise ValueError("Invalid page size")
        # Resolve and reject private or loopback IPs to limit DNS rebinding / SSRF.
        host = urlsplit(url).hostname
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(addr[4][0]).is_global for addr in addresses):
            raise ValueError("Documentation must resolve to public IPs")
        req = Request(url, headers={"User-Agent": "JARVIS-Academy/0.1 (educational research)"})
        fetch = opener or urlopen
        with fetch(req, timeout=12) as response:
            final_url = response.geturl()
            self.check_url(final_url, skill)
            if response.headers.get_content_type() != "text/html":
                raise ValueError("Only HTML documentation is supported")
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError("Documentation page exceeds size limit")
        parser = _PageText()
        parser.feed(raw.decode("utf-8", errors="replace"))
        excerpt = parser.text()[:12000]
        if len(excerpt) < 80:
            raise ValueError("Insufficient educational content")
        title = excerpt[:120]
        self.db.execute("""INSERT INTO academy_sources(url,skill,title,excerpt,fetched_at,reviewed)
            VALUES(?,?,?,?,?,0) ON CONFLICT(url) DO UPDATE SET
            excerpt=excluded.excerpt, fetched_at=excluded.fetched_at, reviewed=0""",
            (final_url, skill, title, excerpt, datetime.now(timezone.utc).isoformat()))
        self.db.commit()
        return {"url": final_url, "skill": skill, "characters": len(excerpt), "reviewed": False}

    def study_notes(self, skill, *, reviewed_only=True, limit=10):
        if skill not in SKILLS or not 1 <= limit <= 30:
            raise ValueError("Invalid study query")
        rows = self.db.execute("""SELECT url,excerpt,reviewed FROM academy_sources
            WHERE skill=? AND (?=0 OR reviewed=1) ORDER BY fetched_at DESC LIMIT ?""",
            (skill, int(reviewed_only), limit))
        return [dict(zip(("url", "excerpt", "reviewed"), row)) for row in rows]

    def review(self, url):
        result = self.db.execute("UPDATE academy_sources SET reviewed=1 WHERE url=?", (url,))
        self.db.commit()
        if result.rowcount != 1:
            raise ValueError("Unknown source")

    def record_exercise(self, skill, passed):
        if skill not in SKILLS or not isinstance(passed, bool):
            raise ValueError("Invalid exercise result")
        self.db.execute("""INSERT INTO academy_progress(skill,completed_exercises,passed_exercises)
            VALUES(?,1,?) ON CONFLICT(skill) DO UPDATE SET
            completed_exercises=completed_exercises+1,
            passed_exercises=passed_exercises+excluded.passed_exercises""", (skill, int(passed)))
        self.db.commit()

    def progress(self):
        counts = {row[0]: {"completed": row[1], "passed": row[2]}
                  for row in self.db.execute("SELECT skill,completed_exercises,passed_exercises FROM academy_progress")}
        return {skill: counts.get(skill, {"completed": 0, "passed": 0}) for skill in SKILLS}

    def close(self):
        self.db.close()
