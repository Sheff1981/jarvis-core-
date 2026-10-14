"""Agent orchestration: plan first, authorize each action, then execute.

No model output is treated as an authorization.
"""
from dataclasses import dataclass
from jarvis.windows_actions import WindowsActions


@dataclass(frozen=True)
class PlannedAction:
    operation: str
    target: str
    reason: str


class AgentCore:
    def __init__(self, actions=None):
        self.actions = actions if actions is not None else WindowsActions()
        self.plan = []
        self.position = 0
        self.pending = None

    def set_plan(self, steps):
        """Accept only supported read-only operations at this stage."""
        if self.pending is not None:
            raise RuntimeError("Resolve the pending permission first")
        checked = []
        for step in steps:
            if step.operation not in ("list_directory", "file_info"):
                raise ValueError("Unsupported agent operation")
            if not step.target or not step.reason:
                raise ValueError("Missing action target or reason")
            checked.append(step)
        if len(checked) > 20:
            raise ValueError("Plan exceeds the 20-step limit")
        self.plan = checked
        self.position = 0

    def next_request(self):
        if self.pending is not None:
            return self.pending
        if self.position >= len(self.plan):
            return None
        step = self.plan[self.position]
        self.pending = self.actions.propose(step.operation, step.target)
        return self.pending

    def resolve(self, token, approved):
        if self.pending is None or token != self.pending.token:
            raise PermissionError("Unknown or expired approval")
        request = self.pending
        self.pending = None
        self.position += 1
        if not approved:
            self.actions.gate.deny(token)
            self.cancel()
            return {"status": "denied"}
        if not self.actions.gate.approve(token):
            raise PermissionError("Approval no longer available")
        try:
            value = self.actions.execute(token, request.operation, request.target)
        except (OSError, ValueError, PermissionError) as exc:
            self.cancel()
            return {"status": "error", "detail": str(exc)}
        return {"status": "completed", "result": value}

    def cancel(self):
        self.actions.gate.revoke_all()
        self.pending = None
        self.plan = []
        self.position = 0
