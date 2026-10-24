"""Security Lab policy tests; no live network access."""
import unittest
from datetime import datetime, timedelta, timezone

from jarvis.security_lab import Scope, SecurityPolicy


class SecurityLabTests(unittest.TestCase):
    def test_pentest_requires_explicit_unexpired_host_scope(self):
        expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        policy = SecurityPolicy(Scope(("example.org",), expiry, True))
        self.assertTrue(policy.authorize("authorized_pentest", "https://example.org/")["allowed"])
        self.assertFalse(policy.authorize("authorized_pentest", "https://other.org/")["allowed"])
        self.assertFalse(policy.authorize("authorized_pentest", "https://sub.example.org/")["allowed"])
        self.assertFalse(SecurityPolicy(Scope(("example.org",), expiry)).authorize(
            "authorized_pentest", "https://example.org/")["allowed"])

    def test_expired_scope_denied(self):
        expiry = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        self.assertFalse(SecurityPolicy(Scope(("example.org",), expiry, True)).authorize(
            "authorized_pentest", "https://example.org/")["allowed"])

    def test_lab_requires_isolation(self):
        policy = SecurityPolicy()
        self.assertFalse(policy.authorize("lab")["allowed"])
        self.assertTrue(policy.authorize("lab", lab_isolated=True)["allowed"])
        self.assertFalse(policy.authorize("unknown")["allowed"])

    def test_onion_research_requires_tor(self):
        self.assertEqual(SecurityPolicy.research_route("http://example.onion", tor_enabled=True), "tor")
        with self.assertRaises(ValueError):
            SecurityPolicy.research_route("http://example.onion")
        with self.assertRaises(ValueError):
            SecurityPolicy.research_route("http://127.0.0.1")
        self.assertEqual(SecurityPolicy.research_route("https://docs.python.org"), "direct")


if __name__ == "__main__":
    unittest.main()
