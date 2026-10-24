"""JARVIS autonomy charter: independent learning, bounded external actions.

External documents and model output are never trusted authorization sources.
Owner authority must be authenticated by the existing owner policy before
granting permissions; the charter itself cannot grant permissions.
"""
from dataclasses import dataclass


LOW_RISK = frozenset({
    "choose_learning_topic", "rank_learning_goals", "read_approved_docs",
    "summarize_research", "propose_ideas", "compare_competitors",
    "draft_code", "run_static_checks",
})
RESTRICTED = frozenset({
    "install_software", "execute_untrusted_code", "change_core",
    "publish_product", "spend_money", "delete_user_data",
    "send_private_data", "scan_external_target", "migrate_memory",
})


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    requires_owner: bool


class AutonomyCharter:
    def __init__(self, *, owner_authorized=False):
        self.owner_authorized = bool(owner_authorized)

    def decide(self, action, *, source="jarvis", within_scope=True):
        if source not in ("jarvis", "owner"):
            return Decision(False, "Untrusted external source cannot issue instructions", False)
        if not within_scope:
            return Decision(False, "Outside approved research or testing scope", False)
        if action in LOW_RISK:
            return Decision(True, "Autonomous low-risk activity", False)
        if action in RESTRICTED:
            if source == "owner" and self.owner_authorized:
                return Decision(True, "Authenticated owner authorization", True)
            return Decision(False, "Authenticated owner authorization required", True)
        return Decision(False, "Unknown action is denied by default", True)
