import unittest
from unittest.mock import patch
from jarvis.permissions import PermissionGate


class PermissionTests(unittest.TestCase):
    def test_pending_approval_expires(self):
        with patch("jarvis.permissions.time.monotonic", return_value=100):
            gate = PermissionGate(ttl_seconds=5)
            request = gate.propose("read", "C:/", "Read disk")
        with patch("jarvis.permissions.time.monotonic", return_value=106):
            self.assertFalse(gate.approve(request.token))

    def test_approved_token_expires_before_execution(self):
        with patch("jarvis.permissions.time.monotonic", return_value=100):
            gate = PermissionGate(ttl_seconds=5)
            request = gate.propose("read", "C:/", "Read disk")
            self.assertTrue(gate.approve(request.token))
        with patch("jarvis.permissions.time.monotonic", return_value=106):
            self.assertFalse(gate.consume(request.token, "read", "C:/"))

    def test_denied_by_default_and_single_use(self):
        gate = PermissionGate()
        request = gate.propose("delete", "C:/tmp/a.txt", "Удалить файл")
        self.assertFalse(gate.consume(request.token, "delete", "C:/tmp/a.txt"))
        self.assertTrue(gate.approve(request.token))
        self.assertTrue(gate.consume(request.token, "delete", "C:/tmp/a.txt"))
        self.assertFalse(gate.consume(request.token, "delete", "C:/tmp/a.txt"))

    def test_approval_cannot_be_reused_for_other_target(self):
        gate = PermissionGate()
        request = gate.propose("read", "C:/private", "Прочитать папку")
        gate.approve(request.token)
        self.assertFalse(gate.consume(request.token, "read", "C:/other"))
        self.assertFalse(gate.consume(request.token, "read", "C:/private"))

    def test_denial_and_revocation(self):
        gate = PermissionGate()
        denied = gate.propose("run", "program.exe", "Запустить")
        self.assertTrue(gate.deny(denied.token))
        self.assertFalse(gate.approve(denied.token))
        approved = gate.propose("run", "program.exe", "Запустить")
        gate.approve(approved.token)
        gate.revoke_all()
        self.assertFalse(gate.consume(approved.token, "run", "program.exe"))


if __name__ == "__main__":
    unittest.main()
