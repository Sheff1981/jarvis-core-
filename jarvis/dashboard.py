"""Dependency-free localhost dashboard for JARVIS."""
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from jarvis.system_metrics import snapshot
from jarvis.growth_planner import GrowthPlanner
from jarvis.projects import Projects
from jarvis.ollama_stream import stream_project
from jarvis.ollama_dialogue import OllamaError

PAGE = Path(__file__).with_name("dashboard.html")


def make_handler(db_path, stream_fn=stream_project):
    token = secrets.token_urlsafe(24)
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
            elif path == "/api/session":
                self._reply(200, json.dumps({"token": token}).encode(), "application/json")
            elif path == "/avatar3d.js":
                self._reply(200, PAGE.with_name("avatar3d.js").read_bytes(), "text/javascript; charset=utf-8")
            elif path == "/api/status":
                data = json.dumps({"service": "JARVIS", "mode": "local",
                                   "dashboard": "online", **snapshot()}).encode()
                self._reply(200, data, "application/json; charset=utf-8")
            elif path == "/api/academy":
                academy = Academy(db_path)
                try:
                    progress = academy.progress()
                finally:
                    academy.close()
                self._reply(200, json.dumps({"skills": progress}, ensure_ascii=False).encode("utf-8"),
                            "application/json; charset=utf-8")
            elif path == "/api/growth":
                assessment = GrowthPlanner().assess(snapshot(), {})
                self._reply(200, json.dumps(assessment.as_dict(), ensure_ascii=False).encode("utf-8"),
                            "application/json; charset=utf-8")
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
            if urlsplit(self.path).path != "/api/chat":
                self._reply(404, b'{"error":"not_found"}', "application/json")
                return
            if self.headers.get("Origin") not in (None, "http://127.0.0.1:" + str(self.server.server_port)):
                self._reply(403, b'{"error":"origin"}', "application/json")
                return
            if not secrets.compare_digest(self.headers.get("X-JARVIS-Token", ""), token):
                self._reply(403, b'{"error":"token"}', "application/json")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= 8192:
                    raise ValueError("length")
                body = json.loads(self.rfile.read(length))
                project_id, question = body["project_id"], body["question"]
                if not isinstance(project_id, str) or len(project_id) > 100:
                    raise ValueError("project")
                if not isinstance(question, str) or not 0 < len(question.strip()) <= 2000:
                    raise ValueError("question")
                db = Projects(db_path)
                try:
                    found = any(p["id"] == project_id for p in db.list(include_done=True))
                finally:
                    db.close()
                if not found:
                    self._reply(404, b'{"error":"project_not_found"}', "application/json")
                    return
            except (ValueError, KeyError, TypeError):
                self._reply(400, b'{"error":"invalid_request"}', "application/json")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                for chunk in stream_fn(project_id, question, db_path=db_path):
                    self.wfile.write((json.dumps({"chunk": chunk}, ensure_ascii=False) + "\n").encode("utf-8"))
                    self.wfile.flush()
                self.wfile.write(b'{"done":true}\n')
                self.wfile.flush()
            except (OllamaError, OSError, ValueError):
                try:
                    self.wfile.write(b'{"error":"ollama_unavailable"}\n')
                    self.wfile.flush()
                except OSError:
                    pass


    return DashboardHandler


def serve(host="127.0.0.1", port=8765, db_path="jarvis.db"):
    if host != "127.0.0.1":
        raise ValueError("Dashboard must bind to localhost")
    server = ThreadingHTTPServer((host, port), make_handler(db_path))
    try:
        server.serve_forever()
    finally:
        server.server_close()
