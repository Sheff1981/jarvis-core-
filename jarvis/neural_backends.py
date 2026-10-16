"""Small, explicit inference backend contracts.

Adapters are opt-in and never download weights or run on import.
"""
from dataclasses import dataclass
import json
from urllib import request


@dataclass(frozen=True)
class InferenceResult:
    text: str
    backend: str


class OllamaAdapter:
    def __init__(self, model, endpoint="http://127.0.0.1:11434/api/generate",
                 timeout=30, transport=None):
        if not model or not endpoint.startswith("http://127.0.0.1:"):
            raise ValueError("local model and loopback endpoint required")
        self.model = model
        self.endpoint = endpoint
        self.timeout = timeout
        self.transport = transport or request.urlopen

    def infer(self, prompt):
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt required")
        payload = json.dumps({"model": self.model, "prompt": prompt,
                              "stream": False}).encode("utf-8")
        outgoing = request.Request(self.endpoint, data=payload,
                                   headers={"Content-Type": "application/json"})
        with self.transport(outgoing, timeout=self.timeout) as response:
            data = json.load(response)
        if not isinstance(data, dict) or not isinstance(data.get("response"), str):
            raise ValueError("invalid Ollama response")
        return InferenceResult(data["response"], "ollama")


class CallableAdapter:
    def __init__(self, callback, backend="local"):
        if not callable(callback) or not backend:
            raise ValueError("callback and backend required")
        self.callback = callback
        self.backend = backend

    def infer(self, prompt):
        text = self.callback(prompt)
        if not isinstance(text, str):
            raise TypeError("backend must return text")
        return InferenceResult(text, self.backend)
