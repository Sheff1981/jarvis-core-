"""Offline tests for unified JARVIS launcher."""
import unittest
from unittest.mock import patch

from jarvis_launcher import main, run


class FakeVoice:
    def __init__(self, path):
        self.path = path

    def listen(self, callback, stop):
        stop.wait(0.01)


class LauncherTests(unittest.TestCase):
    def test_invalid_port_rejected(self):
        with self.assertRaises(ValueError):
            run(port=80)

    def test_dashboard_only_does_not_open_browser(self):
        with patch("jarvis_launcher.serve") as server, patch("jarvis_launcher.webbrowser.open") as browser:
            run()
        server.assert_called_once_with(port=8765, db_path="jarvis.db")
        browser.assert_not_called()

    def test_wake_listener_and_browser_opt_in(self):
        with patch("jarvis_launcher.serve"), patch("jarvis_launcher.webbrowser.open") as browser:
            run(vosk_model="fake-model", open_browser=True, voice_factory=FakeVoice)
        browser.assert_called_once_with("http://127.0.0.1:8765")

    def test_cli_rejects_invalid_port(self):
        with self.assertRaises(ValueError):
            main(["--port", "22"])


if __name__ == "__main__":
    unittest.main()
