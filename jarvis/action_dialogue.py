"""Two-step dialogue for explicit local filesystem approvals."""
import re

from jarvis.windows_actions import WindowsActions


class ActionDialogue:
    def __init__(self, actions=None):
        self.actions = actions if actions is not None else WindowsActions()
        self.pending = None

    def respond(self, phrase):
        phrase = phrase.strip()
        if self.pending is not None:
            request = self.pending
            self.pending = None
            if phrase.casefold() in ("да", "разрешаю", "подтверждаю"):
                if not self.actions.gate.approve(request.token):
                    return "Разрешение больше не действует."
                try:
                    result = self.actions.execute(
                        request.token, request.operation, request.target
                    )
                except (OSError, ValueError, PermissionError) as exc:
                    return "Не удалось выполнить действие: " + str(exc)
                if isinstance(result, list):
                    return "Содержимое папки:\n" + "\n".join(result) if result else "Папка пуста."
                return (
                    f"Файл: {result['name']}; размер: {result['size']} байт; "
                    f"папка: {'да' if result['is_dir'] else 'нет'}."
                )
            self.actions.gate.deny(request.token)
            return "Действие отменено. Для новой операции нужен новый запрос."

        match = re.fullmatch(
            r"(?:покажи содержимое папки|что в папке|список файлов в папке)\s+(.+)",
            phrase, re.IGNORECASE
        )
        operation = "list_directory" if match else None
        if not match:
            match = re.fullmatch(
                r"(?:информация о файле|сведения о файле)\s+(.+)",
                phrase, re.IGNORECASE
            )
            operation = "file_info" if match else None
        if match:
            target = match.group(1).strip().strip('"')
            request = self.actions.propose(operation, target)
            self.pending = request
            return (
                f"Разрешаешь действие {operation} для {request.target}? "
                "Ответь «разрешаю» или «нет»."
            )
        return None

    def close(self):
        self.pending = None
        self.actions.gate.revoke_all()
