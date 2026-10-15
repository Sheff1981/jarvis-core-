"""Streaming local Ollama replies with first-token latency metrics."""
import json
import time
from urllib import request

from jarvis.dialogue_context import build_project_context
from jarvis.dialogue_memory import DialogueMemory
from jarvis.inference_profile import InferenceProfile
from jarvis.ollama_dialogue import OllamaError


def stream_project(project_id, question, *, db_path="jarvis.db", model=None,
                   timeout=120, transport=None, profile=None, clock=None):
    """Yield text chunks; persist a complete exchange only after stream completion.

    The returned generator exposes latency through its StopIteration.value:
    {"first_chunk_seconds": float|None, "total_seconds": float}.
    """
    profile = profile or InferenceProfile()
    model = profile.model if model is None else model
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must not be empty")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("Model must not be empty")
    context = build_project_context(project_id, db_path, limit=profile.history_limit)
    system = ("Ты JARVIS, локальный помощник. Отвечай по-русски. "
              "Не утверждай, что выполнил действия, если не выполнял их. "
              "Проект: {project_name}. Статус: {status}. Следующий шаг: {next_step}.").format(**context)
    messages = [{"role": "system", "content": system}]
    messages.extend(context["messages"])
    messages.append({"role": "user", "content": question.strip()})
    payload = json.dumps({"model": model, "messages": messages, "stream": True,
                          "options": profile.ollama_options()},
                         ensure_ascii=False).encode("utf-8")
    req = request.Request("http://127.0.0.1:11434/api/chat", data=payload,
                          headers={"Content-Type": "application/json"}, method="POST")
    sender = transport or request.urlopen
    now = clock or time.perf_counter
    start = now()
    first = None
    chunks = []
    finished = False
    try:
        with sender(req, timeout=timeout) as response:
            for raw_line in response:
                if not raw_line.strip():
                    continue
                event = json.loads(raw_line)
                if "error" in event:
                    raise OllamaError("Ollama returned an error")
                chunk = event.get("message", {}).get("content", "")
                if chunk:
                    if first is None:
                        first = now() - start
                    chunks.append(chunk)
                    yield chunk
                if event.get("done") is True:
                    finished = True
                    break
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise OllamaError("Local Ollama stream failed") from exc
    if not finished or not "".join(chunks).strip():
        raise OllamaError("Ollama stream ended without a complete answer")
    memory = DialogueMemory(db_path)
    try:
        memory.append(project_id, "user", question)
        memory.append(project_id, "assistant", "".join(chunks))
    finally:
        memory.close()
    return {"first_chunk_seconds": first, "total_seconds": now() - start}
