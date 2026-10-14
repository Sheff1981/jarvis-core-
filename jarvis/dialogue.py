"""A conservative conversational layer with short-lived project context."""
import re
from jarvis.projects import Projects
from jarvis.session import Session, Mode


class Dialogue:
    def __init__(self, db_path="jarvis.db"):
        self.projects = Projects(db_path)
        self.pending_project_id = None
        self.session = Session()

    def respond(self, utterance):
        text = utterance.strip()
        normalized = text.casefold()
        if text:
            self.session.append('user', text)
        if normalized in ('режим беседы', 'разговорный режим', 'давай просто поговорим'):
            self.pending_project_id = None
            self.session.switch(Mode.CONVERSATION)
            return 'Перешёл в разговорный режим. Действия с компьютером отключены.'
        if normalized in ('рабочий режим', 'режим работы'):
            self.pending_project_id = None
            self.session.switch(Mode.WORK)
            return 'Рабочий режим включён. Каждое действие потребует отдельного разрешения.'
        if not text:
            return "Я слушаю."
        if normalized in ("стоп", "джарвис стоп", "джарвис, стоп", "выход"):
            self.pending_project_id = None
            return "Останавливаюсь."
        if normalized in ("отмена", "не запоминай", "джарвис отмена"):
            self.pending_project_id = None
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
        match = re.fullmatch(
            r"(?:джарвис[, ]+)?(?:запомни проект|добавь проект)\s+(.+)",
            text, flags=re.I
        )
        if match:
            name = match.group(1).strip()
            if not name:
                return "Назови проект."
            self.pending_project_id = self.projects.add(name)
            return f"Запомнил проект: {name}. Какой следующий шаг?"
        if self.pending_project_id is not None:
            project_id = self.pending_project_id
            self.pending_project_id = None
            self.projects.update(project_id, next_step=text)
            return f"Следующий шаг записан: {text}."
        if normalized in ("привет", "джарвис привет", "джарвис, привет"):
            return "Привет. Готов продолжать работу."
        return "Пока не умею выполнять эту просьбу. Могу запомнить проект или перечислить незавершённые."

    def close(self):
        self.projects.close()
