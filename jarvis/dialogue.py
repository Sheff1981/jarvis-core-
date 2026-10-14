"""A conservative conversational layer with short-lived project context."""
import re
from jarvis.projects import Projects
from jarvis.session import Session, Mode
from jarvis.local_model import LocalModelError
from jarvis.conversation_memory import ConversationMemory


class Dialogue:
    def __init__(self, db_path="jarvis.db", model=None):
        self.projects = Projects(db_path)
        self.pending_project_id = None
        self.awaiting_project_name = False
        self.session = Session()
        self.model = model
        self.conversation = ConversationMemory(db_path)

    def respond(self, utterance):
        if not isinstance(utterance, str):
            raise TypeError("Utterance must be text")
        text = utterance.strip()
        normalized = text.casefold()
        if text:
            self.session.append('user', text)
        if normalized in ('режим беседы', 'разговорный режим', 'давай просто поговорим'):
            self.pending_project_id = None
            self.session.switch(Mode.CONVERSATION)
            return 'Перешёл в разговорный режим. Действия с компьютером отключены.'
        if normalized in ('рабочий режим', 'режим работы', 'работай'):
            self.pending_project_id = None
            self.session.switch(Mode.WORK)
            return 'Рабочий режим включён. Каждое действие потребует отдельного разрешения.'
        if not text:
            return "Я слушаю."
        if normalized in ("стоп", "джарвис стоп", "джарвис, стоп", "выход"):
            self.pending_project_id = None
            self.awaiting_project_name = False
            self.session.clear()
            return "Останавливаюсь."
        if normalized in ("очисти историю разговора", "забудь наш разговор"):
            self.pending_project_id = None
            self.awaiting_project_name = False
            self.conversation.clear()
            self.session.clear()
            return "История разговора удалена из локальной памяти."
        if normalized in ("отмена", "не запоминай", "джарвис отмена"):
            self.pending_project_id = None
            self.awaiting_project_name = False
            return "Хорошо, ожидающее уточнение отменено."
        if any(phrase in normalized for phrase in (
            "какие проекты", "список проектов", "что не закончено",
            "что у нас не закончено"
        )):
            self.pending_project_id = None
            projects = self.projects.list()
            if not projects:
                return "Незавершённых проектов в моей локальной памяти пока нет."
            return "Незавершённые проекты:\n" + "\n".join(
                f"{i}. {p['name']}. Следующий шаг: {p['next_step'] or 'не определён'}."
                for i, p in enumerate(projects, 1)
            )
        if re.fullmatch(r"(?:джарвис[, ]+)?(?:запомни проект|добавь проект)", text, flags=re.I):
            self.pending_project_id = None
            self.awaiting_project_name = True
            return "Назови проект."
        match = re.fullmatch(
            r"(?:джарвис[, ]+)?(?:запомни проект|добавь проект)\s+(.+)",
            text, flags=re.I
        )
        if match:
            name = match.group(1).strip()
            if not name:
                return "Назови проект."
            self.awaiting_project_name = False
            self.pending_project_id = self.projects.add(name)
            return f"Запомнил проект: {name}. Какой следующий шаг?"
        if self.awaiting_project_name:
            self.awaiting_project_name = False
            self.pending_project_id = self.projects.add(text)
            return f"Запомнил проект: {text}. Какой следующий шаг?"
        if self.pending_project_id is not None:
            project_id = self.pending_project_id
            self.pending_project_id = None
            self.projects.update(project_id, next_step=text)
            return f"Следующий шаг записан: {text}."
        if normalized in ("привет", "джарвис привет", "джарвис, привет"):
            return "Привет. Готов продолжать работу."
        if self.model is not None:
            messages = [{"role": "system", "content": (
                "Ты JARVIS, локальный помощник. Отвечай по-русски. "
                "Ты не выполняешь действия с компьютером через этот канал. "
                "Не утверждай, что совершил действие.")}]
            messages.extend(self.conversation.recent(18))
            messages.append({"role": "user", "content": text})
            try:
                answer = self.model.reply(messages)
            except LocalModelError:
                return "Локальная модель недоступна. Команды памяти продолжают работать."
            self.session.append("assistant", answer)
            self.conversation.append("user", text)
            self.conversation.append("assistant", answer)
            return answer
        return "Пока не умею выполнять эту просьбу. Могу запомнить проект или перечислить незавершённые."

    def close(self):
        self.conversation.close()
        self.projects.close()
