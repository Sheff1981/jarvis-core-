"""Atomic JSON persistence for Neural Core model metadata.

Never executes or downloads models. A failed load leaves the current registry
unchanged. Registry files should be stored in local application data.
"""
import json
import os
from pathlib import Path
import tempfile

from jarvis.model_registry import ModelCard, ModelRegistry


SCHEMA_VERSION = 1


def save_registry(registry, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with registry._lock:
        data = {
            "schema": SCHEMA_VERSION,
            "models": [vars(card).copy() for card in registry._models.values()],
            "active": dict(registry._active),
            "previous": dict(registry._previous),
        }
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent,
            prefix=target.name + ".", suffix=".tmp", delete=False
        ) as handle:
            temporary = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def load_registry(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or data.get("schema") != SCHEMA_VERSION:
        raise ValueError("unsupported model registry schema")
    if not isinstance(data.get("models"), list):
        raise ValueError("invalid model list")
    registry = ModelRegistry()
    for raw in data["models"]:
        if not isinstance(raw, dict):
            raise ValueError("invalid model entry")
        registry.register(ModelCard(**raw))
    for name in ("active", "previous"):
        selected = data.get(name)
        if not isinstance(selected, dict):
            raise ValueError("invalid model selection")
        for model_id, version in selected.items():
            if (model_id, version) not in registry._models:
                raise ValueError("selection references an unknown model version")
    registry._active.update(data["active"])
    registry._previous.update(data["previous"])
    for model_id in registry._previous:
        if model_id not in registry._active:
            raise ValueError("rollback selection without active model")
    return registry
