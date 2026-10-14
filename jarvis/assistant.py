"""One routing point for text and voice: commands first, optional local LLM second."""
from jarvis.dialogue import Dialogue
from jarvis.local_llm import LocalLLM


class Assistant:
    def __init__(self, db_path="jarvis.db", model="qwen2.5:3b", llm=None):
        self.dialogue = Dialogue(db_path)
        self.llm = llm if llm is not None else LocalLLM(model=model)

    def respond(self, phrase):
        answer = self.dialogue.respond(phrase)
        if answer.startswith("Пока не умею"):
            try:
                return self.llm.ask(phrase)
            except RuntimeError as exc:
                return str(exc)
        return answer

    def close(self):
        self.dialogue.close()
