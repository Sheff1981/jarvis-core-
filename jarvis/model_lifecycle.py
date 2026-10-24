"""Explicit lifecycle for optional models; no model loading is performed here."""
from enum import Enum
from threading import RLock


class ModelState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    BUSY = "busy"
    EVICTING = "evicting"


class ModelLifecycle:
    def __init__(self, governor):
        self.governor = governor
        self._lock = RLock()
        self._states = {}
        self._reservations = {}

    def state(self, key):
        with self._lock:
            return self._states.get(key, ModelState.IDLE)

    def begin_load(self, key, estimated_mb):
        with self._lock:
            if self.state(key) != ModelState.IDLE:
                raise RuntimeError("model is not idle")
            reservation = self.governor.reserve(str(key), estimated_mb)
            if reservation is None:
                return False
            self._reservations[key] = reservation
            self._states[key] = ModelState.LOADING
            return True

    def ready(self, key):
        self._transition(key, ModelState.LOADING, ModelState.READY)

    def acquire(self, key):
        self._transition(key, ModelState.READY, ModelState.BUSY)

    def release(self, key):
        self._transition(key, ModelState.BUSY, ModelState.READY)

    def begin_evict(self, key):
        with self._lock:
            if self.state(key) not in (ModelState.LOADING, ModelState.READY):
                raise RuntimeError("model cannot be evicted now")
            self._states[key] = ModelState.EVICTING

    def finish_evict(self, key):
        with self._lock:
            if self.state(key) != ModelState.EVICTING:
                raise RuntimeError("model is not evicting")
            self.governor.release(self._reservations.pop(key))
            self._states.pop(key, None)

    def _transition(self, key, expected, new):
        with self._lock:
            if self.state(key) != expected:
                raise RuntimeError("invalid lifecycle transition")
            self._states[key] = new
