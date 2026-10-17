"""Offline dashboard smoke tests for bundled assets and system telemetry."""
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from jarvis.dashboard import PAGE, make_handler
from jarvis.system_metrics import snapshot


class ControlCenterTests(unittest.TestCase):
    def test_assets_exist_and_no_remote_script_dependency(self):
        root = PAGE.parent
        html = PAGE.read_text(encoding="utf-8")
        js = (root / "dashboard.js").read_text(encoding="utf-8")
        avatar = (root / "avatar3d.js").read_text(encoding="utf-8")
        self.assertIn('id="avatar3d"', html)
        self.assertIn('src="/avatar3d.js"', html)
        self.assertIn('id="chat-form"', html)
        self.assertNotIn("https://", html)
        self.assertIn("AbortController", js)
        self.assertIn("getContext('webgl'", avatar)
        self.assertIn("gl.drawArrays(gl.LINES", avatar)

    def test_metrics_schema(self):
        with patch("urllib.request.urlopen", side_effect=OSError("offline")):
            result = snapshot()
        self.assertEqual(result["ollama"], "offline")
        self.assertIn("cpu_count", result)
        self.assertIn("ram_total_bytes", result)
        self.assertIn("ram_available_bytes", result)

    def test_dashboard_routes_reference_assets(self):
        handler = make_handler(":memory:")
        self.assertTrue(hasattr(handler, "do_GET"))
        self.assertTrue(hasattr(handler, "do_POST"))


if __name__ == "__main__":
    unittest.main()
