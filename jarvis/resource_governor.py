"""Conservative admission control for optional Neural Core workloads.

The governor reserves declared memory budgets. It does not claim to measure
physical RAM or preempt running processes. Voice workloads remain external.
"""
from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True)
class Reservation:
    token: int
    owner: str
    megabytes: int


class ResourceGovernor:
    def __init__(self, budget_mb=384):
        if not isinstance(budget_mb, int) or budget_mb <= 0:
            raise ValueError("budget_mb must be a positive integer")
        self.budget_mb = budget_mb
        self._lock = RLock()
        self._next_token = 0
        self._reservations = {}

    def reserve(self, owner, megabytes):
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("owner must be a nonempty string")
        if not isinstance(megabytes, int) or megabytes <= 0:
            raise ValueError("megabytes must be a positive integer")
        with self._lock:
            if sum(item.megabytes for item in self._reservations.values()) + megabytes > self.budget_mb:
                return None
            self._next_token += 1
            item = Reservation(self._next_token, owner, megabytes)
            self._reservations[item.token] = item
            return item

    def release(self, reservation):
        with self._lock:
            current = self._reservations.get(reservation.token)
            if current != reservation:
                raise ValueError("unknown or stale reservation")
            del self._reservations[reservation.token]

    def snapshot(self):
        with self._lock:
            used = sum(item.megabytes for item in self._reservations.values())
            return {"budget_mb": self.budget_mb, "reserved_mb": used,
                    "available_mb": self.budget_mb - used,
                    "active_reservations": len(self._reservations)}
