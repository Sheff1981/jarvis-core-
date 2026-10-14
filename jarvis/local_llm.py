"""Optional local Ollama conversation backend. No shell or tool execution."""
import json
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


class LocalLLM:
    def __init__(self, model="qwen2.5:3b", endpoint="http://127.0.0.1:11434", timeout=45):
        # Only local loopback is supported: no user data to remote hosts.
        if endpoint not in ("http://127.0.0.1:11434", "http://localhost:11434"):
            raise ValueError("Only the local Ollama endpoint is allowed")
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout

    def ask(self, prompt):
        payload = json.dumps({
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": (
                    "Ты JARVIS, локальный помощник на русском языке. "
                    "Отвечай точно и кратко. Не утверждай, что выполнил действие, "
                    "если не получал подтверждения. Не выдумывай состояние проектов."
                )},
                {"role": "user", "content": prompt},
            ],
        }).encode("utf-8")
        request = Request(
            self.endpoint + "/api/chat", data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.load(response)
        except (URLError, HTTPError, TimeoutError, OSError) as exc:
            raise RuntimeError("Локальная модель недоступна. Проверь Ollama и загрузку модели.") from exc
        try:
            return data["message"]["content"].strip()
        except (KeyError, TypeError, AttributeError) as exc:
            raise RuntimeError("Локальная модель вернула некорректный ответ.") from exc
