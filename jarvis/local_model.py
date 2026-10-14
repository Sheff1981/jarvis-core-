"""Optional local Ollama adapter. No remote hosts, tools, or side effects."""
import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class LocalModelError(RuntimeError):
    pass


class Ollama:
    def __init__(self, model="llama3.2", endpoint="http://127.0.0.1:11434", timeout=15):
        parsed = urlsplit(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1") or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
            raise ValueError("Only local HTTP Ollama endpoints are permitted")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model name required")
        if not isinstance(timeout, (int, float)) or not 0 < timeout <= 120:
            raise ValueError("Timeout must be between 0 and 120 seconds")
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    def reply(self, messages):
        if not isinstance(messages, list) or not messages:
            raise ValueError("Messages required")
        safe = []
        for item in messages[-20:]:
            if not isinstance(item, dict) or item.get("role") not in ("system", "user", "assistant") or not isinstance(item.get("content"), str):
                raise ValueError("Invalid message")
            safe.append({"role": item["role"], "content": item["content"][:8000]})
        payload = json.dumps({"model": self.model, "messages": safe, "stream": False, "options": {"num_predict": 512}}).encode("utf-8")
        request = urllib.request.Request(self.endpoint + "/api/chat", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise LocalModelError("Local model returned an unsuccessful status")
                data = response.read(1024 * 1024 + 1)
                if len(data) > 1024 * 1024:
                    raise LocalModelError("Model response too large")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise LocalModelError("Local model unavailable") from exc
        try:
            answer = json.loads(data)["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise LocalModelError("Invalid model response") from exc
        if not isinstance(answer, str) or not answer.strip():
            raise LocalModelError("Empty model response")
        return answer.strip()
