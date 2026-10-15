"""Two-step dialogue for explicit local filesystem approvals."""
import re

from jarvis.windows_actions import WindowsActions


class ActionDialogue:
    def __init__(self, actions=None):
        self.actions = actions if actions is not None else WindowsActions()
        self.pending = None

    def _log(self, request, status):
        store = self.actions.audit_store
        if store is not None:
            store.record(request.operation, request.target, status)

    def respond(self, phrase):
        phrase = phrase.strip()
        # Vosk sometimes prepends a filler "в" and hears the spoken
        # drive letter C as "це". Normalize only an explicitly requested
        # drive-open phrase; approval is still mandatory.
        voice_drive = re.fullmatch(
            r"(?:в\s+)?(?:открой|открыть|покажи)\s+(?:мне\s+)?"
            r"диск\s+(це|си|с|c|дэ|де|д|d)\s*",
            phrase, re.IGNORECASE
        )
        if voice_drive:
            spoken = voice_drive.group(1).casefold()
            letter = "C" if spoken in ("це", "си", "с", "c") else "D"
            phrase = "открой диск " + letter
        if self.pending is not None:
            request = self.pending
            self.pending = None
            if phrase.casefold() in ("разрешаю", "подтверждаю", "да, разрешаю", "да разрешаю"):
                if not self.actions.gate.approve(request.token):
                    self._log(request, "expired")
                    return "Разрешение больше не действует."
                try:
                    result = self.actions.execute(
                        request.token, request.operation, request.target
                    )
                except (OSError, ValueError, PermissionError) as exc:
                    return "Не удалось выполнить действие: " + str(exc)
                if isinstance(result, dict) and "screen_text" in result:
                    return "Текст на экране:\n" + (result["screen_text"] or "Текст не распознан.")
                if isinstance(result, dict) and result.get("captured"):
                    return "Разовый снимок экрана получен в оперативную память и удалён. Анализ изображения пока не подключён."
                if isinstance(result, dict) and "focused" in result:
                    return "Переключаюсь на окно: " + result["focused"]
                if isinstance(result, dict) and "launched" in result:
                    return "Запускаю приложение: " + result["launched"]
                if isinstance(result, dict) and "opened" in result:
                    return "Открываю в Проводнике: " + result["opened"]
                if request.operation == "list_windows":
                    return "Открытые окна:\n" + "\n".join(result) if result else "Открытых окон с заголовками нет."
                if isinstance(result, list):
                    return "Содержимое папки:\n" + "\n".join(result) if result else "Папка пуста."
                return (
                    f"Файл: {result['name']}; размер: {result['size']} байт; "
                    f"папка: {'да' if result['is_dir'] else 'нет'}."
                )
            self.actions.gate.deny(request.token)
            self._log(request, "denied")
            return "Действие отменено. Для новой операции нужен новый запрос."

        if re.fullmatch(r"(?:джарвис[,! ]+)?(?:прочитай экран|что написано на экране)", phrase, re.IGNORECASE):
            request = self.actions.propose("read_screen_text", "desktop")
            self.pending = request
            self._log(request, "requested")
            return "Разрешаешь разовый снимок и локальное распознавание текста всего экрана? Ответь «разрешаю» или «нет»."

        if re.fullmatch(r"(?:джарвис[,! ]+)?(?:сделай снимок экрана|снимок экрана)", phrase, re.IGNORECASE):
            request = self.actions.propose("capture_screen", "desktop")
            self.pending = request
            self._log(request, "requested")
            return "Разрешаешь разовый снимок всего экрана? Он может содержать личные данные. Ответь «разрешаю» или «нет»."

        focus = re.fullmatch(r"(?:джарвис[,! ]+)?(?:переключись на окно|активируй окно)\s+(.+)", phrase, re.IGNORECASE)
        if focus:
            request = self.actions.propose("focus_window", focus.group(1).strip().strip(chr(34)))
            self.pending = request
            self._log(request, "requested")
            return "Разрешаешь переключиться на окно «" + request.target + "»? Ответь «разрешаю» или «нет»."

        if re.fullmatch(r"(?:джарвис[,! ]+)?(?:покажи открытые окна|какие окна открыты|список открытых окон)", phrase, re.IGNORECASE):
            request = self.actions.propose("list_windows", "desktop")
            self.pending = request
            self._log(request, "requested")
            return "Разрешаешь прочитать заголовки открытых окон? Ответь «разрешаю» или «нет»."

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
        if not match:
            match = re.fullmatch(
                r"(?:джарвис[,! ]+)?(?:открой|открыть|покажи)"
                r"\s+(?:мне\s+)?(?:диск|папку)\s+(.+)",
                phrase, re.IGNORECASE
            )
            operation = "open_explorer" if match else None
        if not match:
            match = re.fullmatch(
                r"(?:джарвис[,! ]+)?(?:открой|запусти|открыть)"
                r"\s+(?:мне\s+)?(?:приложение\s+|программу\s+)?"
                r"(блокнот|калькулятор|проводник)",
                phrase, re.IGNORECASE
            )
            operation = "open_app" if match else None
        if match:
            target = match.group(1).strip().strip('"')
            if operation == "open_explorer" and re.fullmatch(
                r"[a-zа-я]", target, re.IGNORECASE
            ):
                latin = {"с": "C", "д": "D", "е": "E"}
                drive = latin.get(target.casefold(), target.upper())
                target = drive + ":\\"
            if operation == "open_app":
                target = {"блокнот": "notepad", "калькулятор": "calculator",
                          "проводник": "explorer"}[target.casefold()]
            request = self.actions.propose(operation, target)
            self.pending = request
            self._log(request, "requested")
            return (
                f"Разрешаешь действие {operation} для {request.target}? "
                "Ответь «разрешаю» или «нет». Разрешение действует 60 секунд."
            )
        return None

    def close(self):
        self.pending = None
        self.actions.gate.revoke_all()
