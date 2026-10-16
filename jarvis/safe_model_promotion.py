"""Guarded model metadata promotion after explicit evaluation.

Promotion updates registry metadata only, not live inference processes.
"""
from jarvis.model_evaluation import eligible


class SafeModelPromotion:
    def __init__(self, registry):
        self.registry = registry

    def promote(self, model_id, version, evaluation, min_cases=10,
                min_accuracy=0.95):
        self.registry.get(model_id, version)
        if not eligible(evaluation, min_cases=min_cases,
                        min_accuracy=min_accuracy):
            return False
        return self.registry.promote(model_id, version)

    def rollback(self, model_id):
        return self.registry.rollback(model_id)
