"""Conservative inference settings for an 8 GB CPU-only laptop."""
from dataclasses import dataclass


@dataclass(frozen=True)
class InferenceProfile:
    model: str = "qwen2.5:1.5b"
    num_ctx: int = 2048
    num_predict: int = 160
    num_thread: int = 4
    history_limit: int = 6
    temperature: float = 0.3

    def __post_init__(self):
        if not self.model.strip():
            raise ValueError("model is required")
        for key in ("num_ctx", "num_predict", "num_thread", "history_limit"):
            if not isinstance(getattr(self, key), int) or isinstance(getattr(self, key), bool) or getattr(self, key) < 1:
                raise ValueError(key + " must be a positive integer")
        if self.history_limit > 100:
            raise ValueError("history_limit must be at most 100")

    def ollama_options(self):
        return {"num_ctx": self.num_ctx, "num_predict": self.num_predict,
                "num_thread": self.num_thread, "temperature": self.temperature}
