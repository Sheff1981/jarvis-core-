"""Optional local Ollama conversation backend; bounded in-memory dialogue history."""
import json
import time
from urllib.error import URLError, HTTPError
from urllib.request import Request
from jarvis.local_transport import open_local


SYSTEM_PROMPT = (
    "Ты JARVIS, локальный ИИ-помощник на русском языке. "
    "Твоя цель — помогать владельцу с голосовым управлением компьютером, "
    "памятью проектов и дальнейшим развитием автономных функций. "
    "Не выдавай планы и разрабатываемые функции за уже работающие. "
    "Отвечай конкретно, обычно в одном-двух коротких предложениях. "
    "Не утверждай, что выполнил действие, без подтверждения. "
    "Не выдумывай состояние проектов и не заявляй о доступе к интернету, "
    "файлам или приложениям без подключённого инструмента. "
    "Речь распознаётся и озвучивается отдельными модулями."
)


class LocalLLM:
    def __init__(self, model="qwen2.5:3b", endpoint="http://127.0.0.1:11434",
                 timeout=45, max_turns=8, cpu_only=False, keep_alive_seconds=0):
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
        if not isinstance(keep_alive_seconds, int) or isinstance(keep_alive_seconds, bool) or not 0 <= keep_alive_seconds <= 300:
            raise ValueError("keep_alive_seconds must be an integer between 0 and 300")
        self.keep_alive_seconds = keep_alive_seconds
        self.history = []
        self.last_metrics = None
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
            payload_data["keep_alive"] = self.keep_alive_seconds
        payload = json.dumps(payload_data).encode("utf-8")
        request = Request(
            self.endpoint + "/api/chat", data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        started = time.perf_counter()
        self.last_metrics = None
        try:
            with open_local(request, timeout=self.timeout) as response:
                raw = response.read(1024 * 1024 + 1)
                if len(raw) > 1024 * 1024:
                    raise RuntimeError("Локальная модель вернула слишком большой ответ.")
                data = json.loads(raw)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
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
        # Ollama reports nanoseconds; these are timings, not estimates.
        self.last_metrics = {"wall_ms": elapsed_ms}
        for key in ("total_duration", "load_duration", "prompt_eval_duration", "eval_duration"):
            value = data.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                self.last_metrics[key.replace("_duration", "_ms")] = round(value / 1_000_000, 1)
        for key in ("prompt_eval_count", "eval_count"):
            value = data.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                self.last_metrics[key] = value
        # Commit only successful exchanges; failures do not pollute context.
        self.history.extend((
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer},
        ))
        self.history = self.history[-2 * self.max_turns:]
        return answer

    def clear_history(self):
        self.history.clear()
