"""One routing point for text and voice: local commands, then local LLM."""
from jarvis.conversation_store import ConversationStore
from jarvis.dialogue import Dialogue
from jarvis.local_llm import LocalLLM


class Assistant:
    def __init__(self, db_path="jarvis.db", model="qwen2.5:3b", llm=None):
        self.dialogue = Dialogue(db_path)
        self.llm = llm if llm is not None else LocalLLM(model=model)
        self.conversations = ConversationStore(db_path)
        # Restore only bounded context for models supporting a history list.
        if hasattr(self.llm, "history") and hasattr(self.llm, "max_turns"):
            self.llm.history = self.conversations.recent(self.llm.max_turns)

    def respond(self, phrase):
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
