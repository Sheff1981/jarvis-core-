"""Integration tests for local Ollama HTTP isolation (no Ollama installation)."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request

from jarvis.local_transport import open_local


class _Handler(BaseHTTPRequestHandler):
    hits = []

    def do_POST(self):
        self.hits.append(self.path)
        self.send_response(302)
        self.send_header("Location", "http://127.0.0.1:%d/leak" % self.server.server_port)
        self.end_headers()

    def do_GET(self):
        self.hits.append(self.path)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"message": {"content": "leaked"}}).encode())

    def log_message(self, *args):
        pass


class TransportIntegrationTests(unittest.TestCase):
    def test_real_http_redirect_is_not_followed(self):
        _Handler.hits = []
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = "http://127.0.0.1:%d/api/chat" % server.server_port
            with self.assertRaises(HTTPError) as error:
                open_local(Request(url, data=b"{}"), timeout=3)
            self.assertEqual(error.exception.code, 302)
            self.assertEqual(_Handler.hits, ["/api/chat"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
