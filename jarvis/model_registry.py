"""Versioned model metadata registry for optional Neural Core backends.

This registry does not load, download, or execute models.
"""
from dataclasses import dataclass, replace
from threading import RLock


@dataclass(frozen=True)
class ModelCard:
    model_id: str
    version: str
    kind: str
    backend: str
    location: str
    estimated_mb: int


class ModelRegistry:
    def __init__(self):
        self._lock = RLock()
        self._models = {}
        self._active = {}
        self._previous = {}

    def register(self, card):
        if not isinstance(card, ModelCard):
            raise TypeError("ModelCard required")
        if not all((card.model_id, card.version, card.kind, card.backend, card.location)):
            raise ValueError("model metadata must not be empty")
        if not isinstance(card.estimated_mb, int) or card.estimated_mb <= 0:
            raise ValueError("estimated_mb must be positive")
        key = (card.model_id, card.version)
        with self._lock:
            if key in self._models:
                raise ValueError("duplicate model version")
            self._models[key] = card

    def get(self, model_id, version=None):
        with self._lock:
            selected = version if version is not None else self._active.get(model_id)
            if selected is None:
                raise KeyError("no active model")
            return self._models[(model_id, selected)]

    def versions(self, model_id):
        with self._lock:
            return [card for (name, _), card in self._models.items()
                    if name == model_id]

    def promote(self, model_id, version):
        with self._lock:
            if (model_id, version) not in self._models:
                raise KeyError("unknown model version")
            current = self._active.get(model_id)
            if current == version:
                return False
            if current is not None:
                self._previous[model_id] = current
            self._active[model_id] = version
            return True

    def rollback(self, model_id):
        with self._lock:
            previous = self._previous.get(model_id)
            if previous is None:
                raise KeyError("no rollback version")
            current = self._active[model_id]
            self._active[model_id] = previous
            self._previous[model_id] = current
            return self._models[(model_id, previous)]

    def snapshot(self):
        with self._lock:
            return {"registered_versions": len(self._models),
                    "active": dict(self._active),
                    "previous": dict(self._previous)}
