"""Offline tests for the dashboard handler."""
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from jarvis.dashboard import make_handler, serve
from jarvis.projects import Projects


class DashboardTests(unittest.TestCase):
    def test_status_and_projects(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = os.path.join(folder, "jarvis.db")
            projects = Projects(db_path)
            projects.add("JARVIS")
            projects.close()
            handler = make_handler(db_path)
            for path, expected in [("/api/status", "dashboard"), ("/api/projects", "projects")]:
                response = {}
                instance = object.__new__(handler)
                instance.path = path
                instance.wfile = io.BytesIO()
                instance.send_response = lambda status: response.update(status=status)
                instance.send_header = lambda *args: None
                instance.end_headers = lambda: None
                instance.do_GET()
                self.assertEqual(response["status"], 200)
                self.assertIn(expected, json.loads(instance.wfile.getvalue()))

    def test_nonlocal_bind_rejected(self):
        with self.assertRaises(ValueError):
            serve(host="0.0.0.0")


if __name__ == "__main__":
    unittest.main()
