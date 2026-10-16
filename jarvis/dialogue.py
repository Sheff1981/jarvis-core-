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
            self.awaiting_project_name = False
            self.session.switch(Mode.CONVERSATION)
            return 'Перешёл в разговорный режим. Действия с компьютером отключены.'
        if normalized in ('рабочий режим', 'режим работы', 'работай'):
            self.pending_project_id = None
            self.awaiting_project_name = False
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
            self.awaiting_project_name = False
            projects = self.projects.list()
            if not projects:
                return "Незавершённых проектов в моей локальной памяти пока нет."
            return "Незавершённые проекты:\n" + "\n".join(
                f"{i}. {p['name']}. Следующий шаг: {p['next_step'] or 'не определён'}."
                for i, p in enumerate(projects, 1)
            )
        if normalized in ("продолжим проект", "на чём остановились", "на чем остановились"):
            projects = self.projects.list()
            if not projects:
                return "Нет сохранённых незавершённых проектов."
            project = projects[0]
            checkpoint = self.projects.latest_checkpoint(project["id"])
            if checkpoint is None:
                return (f"Проект: {project['name']}. Следующий шаг: "
                        f"{project['next_step'] or 'не определён'}.")
            return (f"Проект: {project['name']}. Этап: {checkpoint['stage']}. "
                    f"Задача: {checkpoint['task']}. Статус: {checkpoint['status']}. "
                    f"Последнее действие: {checkpoint['last_action'] or 'не указано'}. "
                    f"Подтверждение: {checkpoint['evidence'] or 'нет'}. "
                    f"Блокеры: {checkpoint['blockers'] or 'нет'}. "
                    f"Следующий шаг: {checkpoint['next_step'] or 'не определён'}.")
        idea_match = re.fullmatch(
            r"(?:джарвис[, ]+)?(?:идея на потом|отложи идею)\\s+(.+)",
            text, flags=re.I)
        decision_match = re.fullmatch(
            r"(?:джарвис[, ]+)?(?:запиши решение|мы решили)\\s+(.+)",
            text, flags=re.I)
        if idea_match or decision_match:
            projects = self.projects.list()
            if not projects:
                return "Сначала создай проект, к которому относится запись."
            project = projects[0]
            if idea_match:
                idea = idea_match.group(1).strip()
                self.projects.queue_idea(project["id"], idea)
                return (f"Идея сохранена для проекта {project['name']}. "
                        "Текущую задачу не меняю.")
            decision = decision_match.group(1).strip()
            self.projects.record_decision(project["id"], decision)
            return f"Решение сохранено для проекта {project['name']}."
        if normalized in ("отложенные идеи", "список идей"):
            projects = self.projects.list()
            if not projects:
                return "Нет сохранённых проектов."
            ideas = self.projects.ideas(projects[0]["id"])
            queued = [item["idea"] for item in ideas if item["status"] == "queued"]
            return ("Отложенные идеи: " + "; ".join(queued)
                    if queued else "Отложенных идей нет.")
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
                "Сейчас пользователь общается через текстовый chat.py; "
                "голосовой модуль voice_chat.py существует отдельно и не запущен. "
                "Не утверждай, что у тебя есть доступ к интернету, микрофону, "
                "файлам или компьютерным действиям через этот канал. "
                "Не заявляй о выполнении действий без проверки. "
                "Если пользователь хочет голос, объясни, что для него есть "
                "отдельный модуль JARVIS, который требуется настроить и проверить.")}]
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
