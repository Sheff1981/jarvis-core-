"""A safe, deterministic first conversational layer for project memory."""
import re
from jarvis.projects import Projects

class Dialogue:
    def __init__(self, db_path="jarvis.db"):
        self.projects = Projects(db_path)

    def respond(self, utterance):
        text = utterance.strip()
        normalized = text.casefold()
        if not text:
            return "Я слушаю."
        if normalized in ("стоп", "джарвис стоп", "джарвис, стоп", "выход"):
            return "Останавливаюсь."
        if any(phrase in normalized for phrase in ("какие проекты", "список проектов", "что не закончено", "что у нас не закончено")):
            projects = self.projects.list()
            if not projects:
                return "Незавершённых проектов в моей локальной памяти пока нет."
            return "Незавершённые проекты:\n" + "\n".join(
                f"{i}. {p['name']}. Следующий шаг: {p['next_step'] or 'не определён'}."
                for i, p in enumerate(projects, 1)
            )
        match = re.fullmatch(r"(?:джарвис[, ]+)?(?:запомни проект|добавь проект)\s+(.+)", text, flags=re.I)
        if match:
            name = match.group(1).strip()
            if not name:
                return "Назови проект."
            self.projects.add(name)
            return f"Запомнил проект: {name}. Какой следующий шаг?"
        if normalized in ("привет", "джарвис привет", "джарвис, привет"):
            return "Привет. Готов продолжать работу."
        return "Пока не умею выполнять эту просьбу. Могу запомнить проект или перечислить незавершённые."

    def close(self):
        self.projects.close()
