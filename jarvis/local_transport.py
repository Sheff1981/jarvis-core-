"""Shared localhost-only HTTP transport for Ollama.

Redirects are forbidden so a local service cannot forward conversation data
to an external host. The opener deliberately ignores proxy configuration.
"""
from urllib.request import build_opener, HTTPHandler, HTTPRedirectHandler, ProxyHandler


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def open_local(request, timeout):
    opener = build_opener(ProxyHandler({}), HTTPHandler(), _NoRedirect())
    return opener.open(request, timeout=timeout)
