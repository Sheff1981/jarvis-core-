"""Optional local Ollama conversation backend; bounded in-memory dialogue history."""
import json
from urllib.error import URLError, HTTPError
from urllib.request import Request
from jarvis.local_transport import open_local


SYSTEM_PROMPT = (
    "Ты JARVIS, локальный помощник на русском языке. "
    "Отвечай точно и кратко. Не утверждай, что выполнил действие, "
    "если не получал подтверждения. Не выдумывай состояние проектов."
)


class LocalLLM:
    def __init__(self, model="qwen2.5:3b", endpoint="http://127.0.0.1:11434",
                 timeout=45, max_turns=8, cpu_only=False):
        if endpoint not in ("http://127.0.0.1:11434", "http://localhost:11434"):
            raise ValueError("Only the local Ollama endpoint is allowed")
        if not isinstance(max_turns, int) or max_turns < 1:
            raise ValueError("max_turns must be a positive integer")
        if not isinstance(timeout, (int, float)) or not 0 < timeout <= 120:
            raise ValueError("timeout must be between 0 and 120 seconds")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model name is required")
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout
        self.max_turns = max_turns
        if not isinstance(cpu_only, bool):
            raise TypeError("cpu_only must be a boolean")
        self.cpu_only = cpu_only
        self.history = []
        self.mode = 'work'

    def ask(self, prompt):
        if not isinstance(prompt, str):
            raise TypeError("prompt must be text")
        prompt = prompt.strip()[:8000]
        if not prompt:
            return ""
        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT + (" Поддерживай свободную беседу, не предлагай запуск программ." if self.mode == "chat" else " Обсуждай рабочие задачи, не заявляй о выполнении без проверки.")}]
            + self.history[-2 * self.max_turns:]
            + [{"role": "user", "content": prompt}]
        )
        payload_data = {
            "model": self.model,
            "stream": False,
            "messages": messages,
        }
        if self.cpu_only:
            payload_data["options"] = {
                "num_gpu": 0, "num_ctx": 1024,
                "num_predict": 96, "num_thread": 4,
            }
            payload_data["keep_alive"] = 0
        payload = json.dumps(payload_data).encode("utf-8")
        request = Request(
            self.endpoint + "/api/chat", data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with open_local(request, timeout=self.timeout) as response:
                raw = response.read(1024 * 1024 + 1)
                if len(raw) > 1024 * 1024:
                    raise RuntimeError("Локальная модель вернула слишком большой ответ.")
                data = json.loads(raw)
        except (URLError, HTTPError, TimeoutError, OSError) as exc:
            raise RuntimeError("Локальная модель недоступна. Проверь Ollama и загрузку модели.") from exc
        except (ValueError, UnicodeError) as exc:
            raise RuntimeError("Локальная модель вернула повреждённый ответ.") from exc
        try:
            answer = data["message"]["content"].strip()
        except (KeyError, TypeError, AttributeError) as exc:
            raise RuntimeError("Локальная модель вернула некорректный ответ.") from exc
        if not answer:
            raise RuntimeError("Локальная модель вернула пустой ответ.")
        # Commit only successful exchanges; failures do not pollute context.
        self.history.extend((
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer},
        ))
        self.history = self.history[-2 * self.max_turns:]
        return answer

    def clear_history(self):
        self.history.clear()
