"""Bounded priority queue for optional Neural Core jobs.

Scheduling is cooperative: this module never preempts an already running job.
No worker threads are started automatically.
"""
from dataclasses import dataclass, field
from enum import IntEnum
import heapq
import threading
import time


class Priority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    IDLE = 4


@dataclass(order=True)
class ScheduledJob:
    priority: int
    sequence: int
    name: str = field(compare=False)
    callback: object = field(compare=False)
    deadline: float | None = field(default=None, compare=False)
    memory_mb: int = field(default=1, compare=False)


class BackgroundScheduler:
    def __init__(self, governor, max_pending=64):
        if max_pending < 1:
            raise ValueError("max_pending must be positive")
        self.governor = governor
        self.max_pending = max_pending
        self._jobs = []
        self._lock = threading.Lock()
        self._sequence = 0
        self.expired = 0
        self.failed = 0
        self.completed = 0

    def submit(self, name, callback, priority=Priority.LOW,
               deadline=None, memory_mb=1):
        if not callable(callback) or not name:
            raise ValueError("name and callable are required")
        if not isinstance(priority, Priority):
            raise ValueError("priority must be Priority")
        if not isinstance(memory_mb, int) or memory_mb <= 0:
            raise ValueError("memory_mb must be positive")
        with self._lock:
            if len(self._jobs) >= self.max_pending:
                return False
            self._sequence += 1
            heapq.heappush(self._jobs, ScheduledJob(
                priority, self._sequence, name, callback, deadline, memory_mb))
            return True

    def run_next(self):
        with self._lock:
            if not self._jobs:
                return False
            job = heapq.heappop(self._jobs)
        if job.deadline is not None and time.monotonic() > job.deadline:
            self.expired += 1
            return False
        reservation = self.governor.reserve(job.name, job.memory_mb)
        if reservation is None:
            with self._lock:
                heapq.heappush(self._jobs, job)
            return False
        try:
            job.callback()
            self.completed += 1
            return True
        except Exception:
            self.failed += 1
            raise
        finally:
            self.governor.release(reservation)

    def snapshot(self):
        with self._lock:
            pending = len(self._jobs)
        return {"pending": pending, "completed": self.completed,
                "failed": self.failed, "expired": self.expired}
