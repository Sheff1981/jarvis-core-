"""Route local project commands, explicit facts and archive searches before LLM."""
import re

from jarvis.action_audit import ActionAudit
from jarvis.action_dialogue import ActionDialogue
from jarvis.windows_actions import WindowsActions
from jarvis.conversation_store import ConversationStore
from jarvis.dialogue import Dialogue
from jarvis.facts import FactStore
from jarvis.local_llm import LocalLLM
from jarvis.modes import ModeController


FACT_SAVE = re.compile(r"^для проекта (.+?) запомни(?:,? что)? (.+)$", re.IGNORECASE)
FACT_LIST = re.compile(
    r"^(?:что ты помнишь|что помнишь) (?:о|про) проект(?:е)? (.+?)[?.!]*$",
    re.IGNORECASE,
)
FACT_DELETE = re.compile(r"^забудь факт (\d+)$", re.IGNORECASE)
MEMORY_SEARCH = re.compile(
    r"^(?:джарвис[,! ]+)?(?:найди(?: в (?:наших )?разговорах)?|"
    r"поищи(?: в (?:наших )?разговорах)?|"
    r"что мы обсуждали про)\s+(.+?)[?.!]*$", re.IGNORECASE
)


IDENTITY_QUESTION = re.compile(
    r"^(?:(?:ответь (?:мне )?на вопрос|скажи(?: мне)?)[, ]+)?"
    r"(?:кто ты(?: такой)?(?: и зачем)?|"
    r"кто ты и для чего (?:ты )?создан|"
    r"зачем (?:ты )?нужен|"
    r"для чего (?:я )?тебя (?:создал|создаю|конструирую)|"
    r"для чего (?:ты )?создан)"
    r"[?.! ]*$", re.IGNORECASE
)

IDENTITY_ANSWER = (
    "Я Джарвис, твой локальный ИИ-помощник. "
    "Ты создаёшь меня для голосовой работы с компьютером, "
    "памяти проектов и дальнейшего развития самостоятельных функций. "
    "Пока я выполняю только проверенные и разрешённые действия; "
    "полноценное самостоятельное обучение ещё разрабатывается."
)


PROJECT_LIST = re.compile(
    r"^(?:(?:джарвис|слушай джарвис)[,\s]+)?"
    r"(?:какие (?:у нас |мои )?проекты|покажи (?:мои |наши )?проекты|"
    r"перечисли (?:мои |наши )?проекты|список (?:моих |наших )?проектов)"
    r"[?.!\s]*$", re.IGNORECASE
)


class Assistant:
    def __init__(self, db_path="jarvis.db", model="qwen2.5:3b", llm=None):
        self.modes = ModeController()
        self.dialogue = Dialogue(db_path)
        self.action_audit = ActionAudit(db_path)
        self.action_dialogue = ActionDialogue(WindowsActions(audit_store=self.action_audit))
        self.llm = llm if llm is not None else LocalLLM(model=model)
        self.conversations = ConversationStore(db_path)
        self.facts = FactStore(db_path)
        if hasattr(self.llm, "history") and hasattr(self.llm, "max_turns"):
            self.llm.history = self.conversations.recent(self.llm.max_turns)

    def respond(self, phrase):
        if not isinstance(phrase, str):
            raise TypeError("phrase must be text")
        phrase = phrase.strip()
        if not phrase:
            return "Я слушаю."
        if phrase.casefold() in ("очисти историю разговора", "забудь наш разговор"):
            self.clear_conversation()
            return "История разговора удалена из локальной памяти."
        if phrase.casefold() in ("стоп", "джарвис стоп", "джарвис, стоп", "отмена", "джарвис отмена"):
            self.action_dialogue.close()
            return "Ожидающее действие отменено."
        if IDENTITY_QUESTION.fullmatch(phrase):
            return IDENTITY_ANSWER
        mode_reply = self.modes.switch(phrase)
        if mode_reply is not None:
            if hasattr(self.llm, 'mode'):
                self.llm.mode = self.modes.mode
            if self.modes.mode == 'chat':
                self.action_dialogue.close()
            return mode_reply
        # SQLite is authoritative for project inventory, including chat mode.
        if PROJECT_LIST.fullmatch(phrase):
            projects = self.dialogue.projects.list()
            if not projects:
                return "Незавершённых проектов в моей локальной памяти пока нет."
            return "Незавершённые проекты:\n" + "\n".join(
                f"{i}. {p['name']}. Следующий шаг: {p['next_step'] or 'не определён'}."
                for i, p in enumerate(projects, 1)
            )
        if self.modes.mode == 'chat':
            try:
                reply = self.llm.ask(phrase)
            except RuntimeError as exc:
                return str(exc)
            if reply:
                self.conversations.append_exchange(phrase, reply)
            return reply
        action_reply = self.action_dialogue.respond(phrase)
        if action_reply is not None:
            return action_reply
        match = FACT_SAVE.fullmatch(phrase)
        if match:
            project, fact = match.groups()
            fact_id = self.facts.remember(project, fact)
            return f"Запомнил для проекта {project}: {fact} (факт {fact_id})."
        match = FACT_LIST.fullmatch(phrase)
        if match:
            project = match.group(1).strip().rstrip("?.! ")
            facts = self.facts.list(project)
            if not facts:
                return f"Для проекта {project} фактов пока нет."
            return "Факты проекта " + project + ":\n" + "\n".join(
                f"{item['id']}. {item['fact']}" for item in facts[:20]
            )
        match = FACT_DELETE.fullmatch(phrase)
        if match:
            return ("Факт удалён." if self.facts.forget(int(match.group(1)))
                    else "Факт с таким номером не найден.")
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
        self.dialogue.conversation.clear()
        self.dialogue.session.clear()
        self.dialogue.pending_project_id = None
        self.action_dialogue.close()
        if hasattr(self.llm, "clear_history"):
            self.llm.clear_history()

    def close(self):
        self.action_dialogue.close()
        self.action_audit.close()
        self.facts.close()
        self.conversations.close()
        self.dialogue.close()
