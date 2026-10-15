"""Local Ollama dialogue adapter with persistent project context."""
import json
from urllib import request, error

from jarvis.dialogue_context import build_project_context
from jarvis.dialogue_memory import DialogueMemory


class OllamaError(RuntimeError):
    pass


def ask_project(project_id, question, *, db_path="jarvis.db", model="qwen2.5:3b",
                endpoint="http://127.0.0.1:11434/api/chat", timeout=120,
                transport=None):
    """Ask local Ollama; persist both turns only after a valid response."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must not be empty")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("Model must not be empty")
    if endpoint != "http://127.0.0.1:11434/api/chat":
        raise ValueError("Only local Ollama endpoint is supported")
    context = build_project_context(project_id, db_path)
    system = (
        "Ты JARVIS, локальный помощник. Отвечай по-русски. "
        "Не утверждай, что выполнил действия, если не выполнял их. "
        "Название проекта: {name}. Статус: {status}. Следующий шаг: {step}."
    ).format(name=context["project_name"], status=context["status"],
             step=context["next_step"] or "не задан")
    messages = [{"role": "system", "content": system}]
    messages.extend(context["messages"])
    messages.append({"role": "user", "content": question.strip()})
    payload = json.dumps({"model": model, "messages": messages, "stream": False},
                         ensure_ascii=False).encode("utf-8")
    req = request.Request(endpoint, data=payload,
                          headers={"Content-Type": "application/json"}, method="POST")
    sender = transport or request.urlopen
    try:
        with sender(req, timeout=timeout) as response:
            data = json.load(response)
        answer = data["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Empty model response")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise OllamaError("Local Ollama request failed") from exc
    memory = DialogueMemory(db_path)
    try:
        memory.append(project_id, "user", question)
        memory.append(project_id, "assistant", answer)
    finally:
        memory.close()
    return answer
