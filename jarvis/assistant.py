"""One routing point for text and voice: local commands, then local LLM."""
import re

from jarvis.conversation_store import ConversationStore
from jarvis.dialogue import Dialogue
from jarvis.local_llm import LocalLLM


MEMORY_SEARCH = re.compile(
    r"^(?:джарвис[,! ]+)?(?:найди(?: в (?:наших )?разговорах)?|"
    r"поищи(?: в (?:наших )?разговорах)?|"
    r"что мы обсуждали про)\s+(.+?)[?.!]*$", re.IGNORECASE
)


class Assistant:
    def __init__(self, db_path="jarvis.db", model="qwen2.5:3b", llm=None):
        self.dialogue = Dialogue(db_path)
        self.llm = llm if llm is not None else LocalLLM(model=model)
        self.conversations = ConversationStore(db_path)
        if hasattr(self.llm, "history") and hasattr(self.llm, "max_turns"):
            self.llm.history = self.conversations.recent(self.llm.max_turns)

    def respond(self, phrase):
        phrase = phrase.strip()
        match = MEMORY_SEARCH.fullmatch(phrase)
        if match:
            term = match.group(1).strip().rstrip("?.! ")
            if not term:
                return "Уточни, что искать в истории."
            found = self.conversations.search(term, limit=5)
            if not found:
                return "В сохранённых разговорах ничего не найдено."
            return "Нашёл в сохранённых разговорах:\n" + "\n".join(
                ("Вы: " if item["role"] == "user" else "JARVIS: ")
                + item["content"][:350] for item in found
            )
        answer = self.dialogue.respond(phrase)
        if answer.startswith("Пока не умею"):
            try:
                reply = self.llm.ask(phrase)
            except RuntimeError as exc:
                return str(exc)
            if reply:
                self.conversations.append_exchange(phrase, reply)
            return reply
        return answer

    def clear_conversation(self):
        self.conversations.clear()
        if hasattr(self.llm, "clear_history"):
            self.llm.clear_history()

    def close(self):
        self.conversations.close()
        self.dialogue.close()
