"""Local speaker profile persistence: no raw recordings and no cloud.

The embedding extractor is provided separately; this module does not pretend
that acoustic fingerprints are speaker embeddings.
"""
import json
import math
import os
from pathlib import Path
import tempfile


class SpeakerProfileStore:
    def __init__(self, path):
        self.path = Path(path)

    @staticmethod
    def _vector(values):
        if not isinstance(values, (list, tuple)) or not values or len(values) > 4096:
            raise ValueError("invalid speaker embedding")
        if any(isinstance(x, bool) or not isinstance(x, (int, float))
               or not math.isfinite(x) for x in values):
            raise ValueError("speaker embedding must contain finite numbers")
        norm = math.sqrt(sum(float(x) ** 2 for x in values))
        if norm <= 0 or not math.isfinite(norm):
            raise ValueError("speaker embedding norm must be positive")
        return [float(x) / norm for x in values]

    def enroll(self, vectors, model_id):
        if not isinstance(model_id, str) or not model_id.strip():
            raise ValueError("model_id required")
        if not isinstance(vectors, (list, tuple)) or len(vectors) < 3:
            raise ValueError("at least three enrollment samples required")
        normalized = [self._vector(v) for v in vectors]
        width = len(normalized[0])
        if any(len(v) != width for v in normalized):
            raise ValueError("embedding dimensions differ")
        centroid = self._vector([sum(v[i] for v in normalized) for i in range(width)])
        data = {"version": 1, "model_id": model_id, "samples": len(normalized),
                "embedding": centroid}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=str(self.path.parent),
                prefix=".speaker-", suffix=".tmp", delete=False
            ) as file:
                tmp_path = Path(file.name)
                json.dump(data, file, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(tmp_path, self.path)
            if os.name != "nt":
                self.path.chmod(0o600)
        finally:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink()
        return data

    def load(self, model_id):
        if not self.path.is_file():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("version") != 1 or data.get("model_id") != model_id:
            raise ValueError("speaker profile model mismatch")
        vector = self._vector(data["embedding"])
        if data.get("samples", 0) < 3:
            raise ValueError("invalid enrollment sample count")
        return vector

    def delete(self):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


class CosineSpeakerVerifier:
    def __init__(self, profile_store, extractor, model_id, threshold=0.78):
        if not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 < threshold <= 1:
            raise ValueError("invalid similarity threshold")
        self.store = profile_store
        self.extractor = extractor
        self.model_id = model_id
        self.threshold = float(threshold)

    def __call__(self, pcm16, sample_rate):
        profile = self.store.load(self.model_id)
        if profile is None:
            return False
        probe = self.store._vector(self.extractor(pcm16, sample_rate))
        if len(probe) != len(profile):
            return False
        similarity = sum(a * b for a, b in zip(profile, probe))
        return similarity >= self.threshold
