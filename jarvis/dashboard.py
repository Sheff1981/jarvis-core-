"""Dependency-free localhost dashboard for JARVIS."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from jarvis.projects import Projects

PAGE = Path(__file__).with_name("dashboard.html")


def make_handler(db_path):
    class DashboardHandler(BaseHTTPRequestHandler):
        def _reply(self, status, data, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/":
                self._reply(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif path == "/api/status":
                data = json.dumps({"service": "JARVIS", "mode": "local",
                                   "dashboard": "online", "ollama": "not_checked"}).encode()
                self._reply(200, data, "application/json; charset=utf-8")
            elif path == "/api/projects":
                db = Projects(db_path)
                try:
                    projects = db.list(include_done=True)
                finally:
                    db.close()
                self._reply(200, json.dumps({"projects": projects}, ensure_ascii=False).encode("utf-8"),
                            "application/json; charset=utf-8")
            elif path == "/dashboard.js":
                script = PAGE.with_name("dashboard.js").read_bytes()
                self._reply(200, script, "text/javascript; charset=utf-8")
            else:
                self._reply(404, b'{"error":"not_found"}', "application/json")

        def do_POST(self):
            self._reply(405, b'{"error":"read_only"}', "application/json")

    return DashboardHandler


def serve(host="127.0.0.1", port=8765, db_path="jarvis.db"):
    if host != "127.0.0.1":
        raise ValueError("Dashboard must bind to localhost")
    server = ThreadingHTTPServer((host, port), make_handler(db_path))
    try:
        server.serve_forever()
    finally:
        server.server_close()
