"""Opt-in inference facade: no automatic model loading or voice routing."""
from threading import RLock

from jarvis.model_lifecycle import ModelState
from jarvis.neural_telemetry import measured_inference


class NeuralRuntime:
    def __init__(self, controller):
        self.controller = controller
        self._lock = RLock()
        self._adapters = {}

    def attach(self, model_id, version, adapter):
        if not callable(getattr(adapter, "infer", None)):
            raise TypeError("adapter must implement infer")
        with self._lock, self.controller._lock:
            key = (model_id, version)
            self.controller.registry.get(model_id, version)
            if self.controller.lifecycle.state(key) != ModelState.READY:
                raise RuntimeError("model metadata must be ready")
            self._adapters[key] = adapter

    def infer(self, model_id, prompt, *, measure=False):
        with self._lock, self.controller._lock:
            card = self.controller.registry.get(model_id)
            key = (model_id, card.version)
            adapter = self._adapters.get(key)
            if adapter is None:
                raise RuntimeError("active backend is not attached")
            self.controller.lifecycle.acquire(key)
        try:
            if measure:
                return measured_inference(adapter, prompt)
            return adapter.infer(prompt)
        finally:
            with self._lock, self.controller._lock:
                self.controller.lifecycle.release(key)

    def detach(self, model_id, version):
        with self._lock, self.controller._lock:
            key = (model_id, version)
            if self.controller.registry.snapshot()["active"].get(model_id) == version:
                raise RuntimeError("cannot detach active backend")
            if self.controller.lifecycle.state(key) == ModelState.BUSY:
                raise RuntimeError("cannot detach busy backend")
            self._adapters.pop(key, None)
