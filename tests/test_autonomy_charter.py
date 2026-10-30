"""Autonomy charter permission and prompt-injection boundaries."""
import unittest
from jarvis.autonomy_charter import AutonomyCharter


class AutonomyCharterTests(unittest.TestCase):
    def test_autonomous_learning_without_owner_prompt(self):
        policy = AutonomyCharter()
        for action in ("choose_learning_topic", "read_approved_docs", "propose_ideas"):
            decision = policy.decide(action)
            self.assertTrue(decision.allowed)
            self.assertFalse(decision.requires_owner)

    def test_sensitive_actions_require_authenticated_owner(self):
        policy = AutonomyCharter()
        for action in ("change_core", "spend_money", "scan_external_target"):
            self.assertFalse(policy.decide(action).allowed)
            self.assertFalse(policy.decide(action, source="owner").allowed)
            self.assertTrue(AutonomyCharter(owner_authorized=True).decide(
                action, source="owner").allowed)

    def test_external_pages_cannot_grant_permissions(self):
        policy = AutonomyCharter(owner_authorized=True)
        self.assertFalse(policy.decide("change_core", source="website").allowed)
        self.assertFalse(policy.decide("read_approved_docs", source="website").allowed)
        self.assertFalse(policy.decide("choose_learning_topic", within_scope=False).allowed)

    def test_unknown_actions_denied(self):
        self.assertFalse(AutonomyCharter().decide("unknown_action").allowed)


if __name__ == "__main__":
    unittest.main()
