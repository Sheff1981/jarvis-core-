import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

from jarvis.local_transport import open_local


class LocalTransportTests(unittest.TestCase):
    def test_redirect_is_rejected(self):
        request = Request("http://127.0.0.1:11434/api/chat", data=b"{}")
        with patch("jarvis.local_transport.build_opener") as build:
            opener = build.return_value
            opener.open.side_effect = HTTPError(
                request.full_url, 302, "redirect", {"Location": "https://example.com"}, None)
            with self.assertRaises(HTTPError):
                open_local(request, timeout=1)
            args = build.call_args.args
            self.assertTrue(any(type(handler).__name__ == "_NoRedirect" for handler in args))
            self.assertTrue(any(type(handler).__name__ == "ProxyHandler" and handler.proxies == {} for handler in args))

    def test_timeout_is_forwarded(self):
        request = Request("http://127.0.0.1:11434/api/chat", data=b"{}")
        with patch("jarvis.local_transport.build_opener") as build:
            open_local(request, timeout=7)
            self.assertEqual(build.return_value.open.call_args.kwargs["timeout"], 7)
