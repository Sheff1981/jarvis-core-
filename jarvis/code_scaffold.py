"""Create a fixed Telegram bot source-code starter only after explicit approval.

Never runs generated code or opens network connections. No existing file is overwritten.
"""
from pathlib import Path
import re


BOT_SOURCE = '''"""Basic Telegram echo bot. Standard library only; started manually."""
import json
import os
import time
from urllib.parse import urlencode
from urllib.request import urlopen

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

if not TOKEN or not CHAT_ID or not CHAT_ID.lstrip("-").isdigit():
    raise SystemExit("Set TELEGRAM_BOT_TOKEN and numeric TELEGRAM_CHAT_ID")

BASE_URL = "https://api.telegram.org/bot" + TOKEN + "/"


def api(method, parameters):
    encoded = urlencode(parameters).encode("utf-8")
    with urlopen(BASE_URL + method, data=encoded, timeout=40) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError("Telegram API returned an error")
    return result["result"]


def main():
    offset = 0
    print("Telegram bot running; Ctrl+C to stop")
    while True:
        try:
            updates = api("getUpdates", {"offset": offset, "timeout": 25})
            for update in updates:
                offset = max(offset, int(update["update_id"]) + 1)
                message = update.get("message", {})
                chat = message.get("chat", {})
                chat_id = str(chat.get("id", ""))
                text = message.get("text")
                if chat_id != CHAT_ID or not isinstance(text, str):
                    continue
                reply = "Бот работает. Вы написали: " + text[:1000]
                api("sendMessage", {"chat_id": CHAT_ID, "text": reply})
        except KeyboardInterrupt:
            break
        except (OSError, ValueError, KeyError) as exc:
            print("Telegram connection error:", type(exc).__name__)
            time.sleep(3)


if __name__ == "__main__":
    main()
'''

README = """# Telegram echo bot starter

This is a locally generated, untested starter project. JARVIS did not
start the bot, register a Telegram account, or connect to Telegram.

1. Create a bot via the official @BotFather, and keep its token private.
2. Obtain your numeric Telegram chat ID.
3. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your own PowerShell session.
4. Run `python bot.py` in this folder.

No extra Python packages are required. This bot only replies to the specified
chat ID. Stop with Ctrl+C. Never publish the token in source code or Git.
"""


class CodeDraftDialogue:
    """Voice-specific fixed-template generation with a two-turn permission gate."""

    def __init__(self, db_path):
        db = Path(db_path).resolve()
        workspace = db.parent.parent if db.parent.name.lower() == "data" else db.parent
        self.output_root = workspace / "generated"
        self.pending = False

    @staticmethod
    def _requested(phrase):
        text = phrase.casefold()
        return (bool(re.search(r"\b(?:создай|создал|сделай|написал|напиши|сгенерируй)\b", text))
                and bool(re.search(r"бот", text))
                and bool(re.search(r"телеграм|telegram", text)))

    def respond(self, phrase):
        text = phrase.strip().casefold()
        if self.pending:
            if text in ("разрешаю", "подтверждаю", "да разрешаю", "да, разрешаю"):
                self.pending = False
                try:
                    path = self._create()
                except (OSError, ValueError) as exc:
                    return "Создать исходники не удалось: " + str(exc)
                return "Созданы исходники простого Telegram-бота в папке " + str(path) + ". Бот не запущен. Инструкция находится в файле README."
            if ("кодом" in text or "исходный код" in text) and len(text) < 120:
                return "Да, создам исходный код Telegram-бота. Разрешаешь записать новый проект? Ответь «разрешаю» или «нет»."
            self.pending = False
            return "Создание Telegram-бота отменено. Файлы не изменены."

        if self._requested(phrase):
            self.pending = True
            return ("Могу создать исходники простого Telegram-бота в отдельной папке. "
                    "Ничего не запускаю и не меняю существующие проекты. "
                    "Разрешаешь? Ответь «разрешаю» или «нет».")
        return None

    def _create(self):
        root = self.output_root
        if root.is_symlink():
            raise ValueError("Папка generated является ссылкой")
        if root.exists() and not root.is_dir():
            raise ValueError("Путь generated занят файлом")
        root.mkdir(parents=True, exist_ok=True)
        target = root / "telegram_echo_bot"
        # Exclusive creation prevents replacing existing user projects.
        target.mkdir(exist_ok=False)
        try:
            compile(BOT_SOURCE, "bot.py", "exec")
            for name, data in (("bot.py", BOT_SOURCE), ("README.md", README)):
                with (target / name).open("x", encoding="utf-8", newline="\n") as file:
                    file.write(data)
        except BaseException:
            for name in ("bot.py", "README.md"):
                f = target / name
                if f.is_file() and not f.is_symlink():
                    f.unlink()
            target.rmdir()
            raise
        return target

    def close(self):
        self.pending = False
