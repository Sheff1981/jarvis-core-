"""Coordinated metadata activation and model lifecycle.

This controller does not load inference weights or switch live Ollama.
"""
from threading import RLock

from jarvis.model_lifecycle import ModelLifecycle, ModelState
from jarvis.safe_model_promotion import SafeModelPromotion


class NeuralModelController:
    def __init__(self, registry, governor):
        self.registry = registry
        self.lifecycle = ModelLifecycle(governor)
        self.promotion = SafeModelPromotion(registry)
        self._lock = RLock()

    def prepare(self, model_id, version):
        with self._lock:
            card = self.registry.get(model_id, version)
            return self.lifecycle.begin_load((model_id, version), card.estimated_mb)

    def mark_ready(self, model_id, version):
        with self._lock:
            self.lifecycle.ready((model_id, version))

    def activate(self, model_id, version, evaluation):
        with self._lock:
            if self.lifecycle.state((model_id, version)) != ModelState.READY:
                return False
            return self.promotion.promote(model_id, version, evaluation)

    def unload(self, model_id, version):
        with self._lock:
            key = (model_id, version)
            if self.registry.snapshot()["active"].get(model_id) == version:
                raise RuntimeError("cannot unload active model")
            self.lifecycle.begin_evict(key)
            self.lifecycle.finish_evict(key)

    def rollback(self, model_id):
        with self._lock:
            previous = self.registry.snapshot()["previous"].get(model_id)
            if previous is None or self.lifecycle.state((model_id, previous)) != ModelState.READY:
                raise RuntimeError("rollback target is not ready")
            return self.promotion.rollback(model_id)
