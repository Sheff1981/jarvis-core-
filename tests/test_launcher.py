"""Offline tests for unified JARVIS launcher."""
import unittest
from unittest.mock import patch, Mock

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
        with patch("jarvis_launcher.serve"), patch("jarvis_launcher.open_when_ready") as ready:
            run(vosk_model="fake-model", open_browser=True, voice_factory=FakeVoice)
        ready.assert_called_once()
        self.assertEqual(ready.call_args.args[0], "http://127.0.0.1:8765")

    def test_browser_waits_for_server(self):
        from jarvis_launcher import open_when_ready
        import threading
        response = Mock()
        response.status = 200
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opened = []
        with patch("jarvis_launcher.urllib.request.urlopen", return_value=response):
            self.assertTrue(open_when_ready("http://127.0.0.1:8765", threading.Event(), opener=opened.append))
        self.assertEqual(opened, ["http://127.0.0.1:8765"])

    def test_second_instance_is_not_started(self):
        import socket
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        try:
            with patch("jarvis_launcher.serve") as server:
                self.assertFalse(run(port=port))
                server.assert_not_called()
        finally:
            sock.close()

    def test_cli_rejects_invalid_port(self):
        with self.assertRaises(ValueError):
            main(["--port", "22"])


if __name__ == "__main__":
    unittest.main()
