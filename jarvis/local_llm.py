"""Optional local Ollama conversation backend; bounded in-memory dialogue history."""
import json
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


SYSTEM_PROMPT = (
    "Ты JARVIS, локальный помощник на русском языке. "
    "Отвечай точно и кратко. Не утверждай, что выполнил действие, "
    "если не получал подтверждения. Не выдумывай состояние проектов."
)


class LocalLLM:
    def __init__(self, model="qwen2.5:3b", endpoint="http://127.0.0.1:11434",
                 timeout=45, max_turns=8):
        if endpoint not in ("http://127.0.0.1:11434", "http://localhost:11434"):
            raise ValueError("Only the local Ollama endpoint is allowed")
        if not isinstance(max_turns, int) or max_turns < 1:
            raise ValueError("max_turns must be a positive integer")
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout
        self.max_turns = max_turns
        self.history = []
        self.mode = 'work'

    def ask(self, prompt):
        prompt = prompt.strip()
        if not prompt:
            return ""
        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT + (" Поддерживай свободную беседу, не предлагай запуск программ." if self.mode == "chat" else " Обсуждай рабочие задачи, не заявляй о выполнении без проверки.")}]
            + self.history
            + [{"role": "user", "content": prompt}]
        )
        payload = json.dumps({
            "model": self.model,
            "stream": False,
            "messages": messages,
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
